package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
//	"os"
//	"bytes"
	"regexp"
	"strings"
	"log"
	"math"
	"runtime"
//	"runtime/pprof"
	"sort"
	"strconv"
	"flag"
)

type loadedRecord struct {
	id, key_title, key, original_key string
	matched                          bool
	trigrams                         []string
	trigrams_int                     []int
	length                           int
}

type recordList []loadedRecord

func (r recordList) Len() int           { return len(r) }
func (r recordList) Less(i, j int) bool { return len(r[i].key) < len(r[j].key) }
func (r recordList) Swap(i, j int)      { r[i], r[j] = r[j], r[i] }

type trigramList struct {
	freq_count map[string]int
	list       []string
}

func (tl trigramList) Len() int { return len(tl.list) }
func (tl trigramList) Less(i, j int) bool {
	if tl.freq_count[tl.list[i]] == tl.freq_count[tl.list[j]] {
		return tl.list[i] < tl.list[j]
	}
	return tl.freq_count[tl.list[i]] < tl.freq_count[tl.list[j]]
}
func (tl trigramList) Swap(i, j int) { tl.list[i], tl.list[j] = tl.list[j], tl.list[i] }

type recordPos struct {
	value, pos int
}


func create_trigram(key string, length int) []string {
	record := make([]string, 0)
	var recordcount map[string]int

	if length < 1 {
		recordcount = make(map[string]int)
		recordcount[key] = 1
	} else {
		recordcount = make(map[string]int)
		for i := 0; i < length; i++ {
			recordcount[key[i:i+3]] += 1
		}
	}

	for trigram, count := range recordcount {
		record = append(record, trigram)
		for i := 1; i < count; i++ {
			record = append(record, trigram+strconv.FormatInt(int64(i), 10))
		}
	}
	//sort.Strings(record)
	return record
}

func get_similarity(current_trigrams, matching_trigrams []int, current_length, matching_length int) float64 {
	current_i := 0
	match_i := 0
	similar_trigrams := 0.0
	for {
		if current_i >= current_length || match_i >= matching_length {
			break
		}
		current_trigram := current_trigrams[current_i]
		matching_trigram := matching_trigrams[match_i]
		//compare := compare_strings(current_trigram, matching_trigram)
		if current_trigram > matching_trigram {
			match_i += 1
		} else if current_trigram < matching_trigram {
			current_i += 1
		} else {
			current_i += 1
			match_i += 1
			similar_trigrams += 1.0
		}
	}
	similarity := (similar_trigrams * 2.0) / (float64(matching_length + current_length))
	return similarity
}

func read_record(csv_reader *csv.Reader) (loadedRecord, error) {
	row, err := csv_reader.Read()
	if err != nil {
		return loadedRecord{}, err
	}
	if err != nil {
		panic(err)
	}
	var id, key string
	if len(row) == 2 {
		id, key = row[0], row[1]
	} else {
		key = row[0]
	}

	numeric, _ := regexp.Compile("[0-9]")
	new_key := numeric.ReplaceAllString(key, "")
	new_key = strings.ToLower(new_key)

	record := loadedRecord{
		id:           id,
		key:          new_key,
		original_key: key,
		length:       len(new_key) - 2,
	}
	record.trigrams = create_trigram(new_key, record.length)

	return record, nil
}

func cluster(w http.ResponseWriter, r *http.Request) {

	key := r.Form["similarity"]
	max_similarity := 0.8
	var err error
	if len(key) > 0 {
		max_similarity, err = strconv.ParseFloat(key[0], 64)
		if err != nil {
			w.WriteHeader(400)
			w.Write([]byte("similarity not a number"))
			return
		}
	}

	key = r.Form["format"]
	format := "table"
	if len(key) > 0 {
		format = key[0]
	}

	var reader io.Reader

	key = r.Form["url"]
	if len(key) > 0 {
		url := key[0]
		response, err := http.Get(url)
		if err != nil || response.StatusCode != 200 {
			w.WriteHeader(400)
			w.Write([]byte("bad url could not fetch"))
			return
		}
		reader = response.Body
		defer response.Body.Close()
	} else {
		reader = r.Body
		defer r.Body.Close()
	}

//	f, _ := os.Create("cpu_profile")
//	pprof.StartCPUProfile(f)
//	defer pprof.StopCPUProfile()

	var writer io.Writer = w
//	count := 0
	match_count := 0
	csv_reader := csv.NewReader(reader)
	csv_writer := csv.NewWriter(writer)
	record_list := make(recordList, 0)
	reverse_lookup := make(map[int][]recordPos)
	trigram_index := make(map[string]int)
	all_trigrams := make([]string, 0)

	total_trigrams := 0
	for {
		record, err := read_record(csv_reader)

		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		total_trigrams += record.length
		if total_trigrams > 5000000 {
			w.WriteHeader(400)
			w.Write([]byte("file too big"))
			return
		}
		for _, trigram := range record.trigrams {
			trigram_index[trigram] += 1
		}
		record_list = append(record_list, record)
	}

	all_trigrams = make([]string, 0)
	for trigram, _ := range trigram_index {
		all_trigrams = append(all_trigrams, trigram)
	}

	sort.Sort(record_list)
	sort.Sort(trigramList{trigram_index, all_trigrams})

	for index, trigram := range all_trigrams {
		trigram_index[trigram] = index
	}

	for num := range record_list {
		record := &record_list[num]
		record.trigrams_int = make([]int, len(record.trigrams))
		for num, trigram := range record.trigrams {
			record.trigrams_int[num] = trigram_index[trigram]
		}
		sort.IntSlice(record.trigrams_int).Sort()
		record.trigrams = nil
	}

	for index := range record_list {
		record := &record_list[index]
		prefix_len := int(float64(record.length) + 3 - math.Ceil((max_similarity*float64(record.length))/(2-max_similarity)))

		if record.id == "" {record.id = strconv.FormatInt(int64(index), 10)}

		for i := 0; i < prefix_len && i < record.length; i++ {
			trigram := record.trigrams_int[i]
			reverse_lookup[trigram] = append(reverse_lookup[trigram], recordPos{index, i + 1})
		}
	}

	log.Println(max_similarity, format, len(record_list), total_trigrams)

	//for k,v := range reverse_lookup {
//			fmt.Println(k,":",v)
//		}
	//fmt.Println("index ", trigram_index)
	//fmt.Println(reverse_lookup)

	//var matching_lists [][]recordPos

	for current_id := 0; current_id < len(record_list); current_id++ {


		current_record := record_list[current_id]
		candidates := make(map[int]int, 1000)
		prefix_len := int(float64(current_record.length) + 3 - math.Ceil((max_similarity*float64(current_record.length))/(2-max_similarity)))

		//fmt.Println(current_record.key, current_id, current_record.trigrams)
		//fmt.Println(current_id, current_record)
		//matching_lists = make([][]recordPos, len(current_record.trigrams))
		for pos := 0; pos < prefix_len && pos < current_record.length; pos++ {
			trigram := current_record.trigrams_int[pos]
			//			fmt.Println(trigram)
			trigram_slice := reverse_lookup[trigram]
			if len(trigram_slice) > 0 {
				reverse_lookup[trigram] = trigram_slice[1:]
			}
		}
		if current_record.matched {
			continue
		}
		if format == "table" {
			csv_writer.Write([]string{current_record.id, current_record.original_key, current_record.original_key, current_record.id})
		}
		//fmt.Println(reverse_lookup)

		for pos := 0; pos < prefix_len && pos < current_record.length; pos++ {
			trigram := current_record.trigrams_int[pos]
			matching_list := reverse_lookup[trigram]

			for i := 0; i < len(matching_list); i++ {
				matching_pos := matching_list[i]
				matching_record := record_list[matching_pos.value]
				if float64(matching_record.length) > float64(current_record.length)*((2-max_similarity)/max_similarity) {
					break
				}
				if matching_record.matched {
					continue
				}

				//alpha := max_similarity * (float64(current_record.length) + float64(matching_record.length)) / 2
				//ubound := 1 + math.Min(float64(current_record.length - pos + 1), float64(matching_record.length - matching_pos.pos))

				//fmt.Println(candidates[matching_pos.value], "+", ubound, ">=", alpha)
				candidates[matching_pos.value] = candidates[matching_pos.value] + 1

				//new_value := candidates[matching_pos.value]
				//if float64(new_value) + ubound >= alpha {
				//		candidates[matching_pos.value] = new_value + 1
				//	} else {
				//		delete(candidates, matching_pos.value)
				//	}
			}
		}
		matched := false
		//fmt.Println(candidates)
		for key, count := range candidates {
			if count < 3 {
				continue
			}
			similarity := get_similarity(current_record.trigrams_int, record_list[key].trigrams_int, current_record.length, record_list[key].length)
			if similarity > max_similarity {
				match_count += 1
				record_list[key].matched = true
				if format == "table" {
					csv_writer.Write([]string{current_record.id, current_record.original_key, record_list[key].original_key, record_list[key].id})
				}

				if format == "match" {
					if matched == false {
						w.Write([]byte(fmt.Sprintf("---match---%d\n", match_count)))
						w.Write([]byte(current_record.original_key + "\n"))
						matched = true
					}
					w.Write([]byte(record_list[key].original_key + "\n"))
				}
			}
		}
		if format == "match" {
			if matched {
				w.Write([]byte("--------------\n"))
			}
		}

	}
	csv_writer.Flush()
	return
}


type LimitedHandler struct {
	semaphore chan int
}

func (handler LimitedHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	<-handler.semaphore
	log.Println("started ", r.URL)
	defer func() {
		handler.semaphore <- 1
		runtime.GC()
		log.Println("finshed", r.URL)
	}()

	switch r.URL.Path[1:] {
	case "cluster":
		cluster(w, r)
	default:
		w.WriteHeader(400)
		w.Write([]byte("Command not found"))
	}
	defer r.Body.Close()
//	f, err := os.Create("memprofile")
 //   if err != nil {
//		log.Fatal(err)
//	}
//	pprof.WriteHeapProfile(f)
//	f.Close()
}

func main() {
	port := flag.String("port", "9999", "port to serve")
	procs := flag.Int("procs", 0, "port to serve")
	flag.Parse()
	maxprocs := *procs
	if maxprocs == 0 {
		maxprocs = runtime.NumCPU()
	}

	semaphore := make(chan int, maxprocs)
	runtime.GOMAXPROCS(maxprocs)
	for i := 0; i < maxprocs; i++ {
		semaphore <- 1
	}

	handler := LimitedHandler{semaphore}
	http.Handle("/", handler)

	log.Println("Running webserver on port ", *port, " with max procs ", maxprocs)

//	defer func () {
//	f, err := os.Create("memprofile")
 //   if err != nil {
//		log.Fatal(err)
//	}
//	pprof.WriteHeapProfile(f)
//	f.Close()
//	} ()

	http.ListenAndServe(":" + *port, nil)


}

