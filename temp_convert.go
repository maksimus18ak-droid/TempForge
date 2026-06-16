// temp_convert.go - Конвертер температур на Go (CLI)
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
)

type Scale struct {
	ToKelvin   func(float64) float64
	FromKelvin func(float64) float64
	Name       string
	Symbol     string
}

var scales = map[string]Scale{
	"c": {
		ToKelvin:   func(x float64) float64 { return x + 273.15 },
		FromKelvin: func(x float64) float64 { return x - 273.15 },
		Name:       "Цельсий", Symbol: "°C",
	},
	"f": {
		ToKelvin:   func(x float64) float64 { return (x-32)*5/9 + 273.15 },
		FromKelvin: func(x float64) float64 { return (x-273.15)*9/5 + 32 },
		Name:       "Фаренгейт", Symbol: "°F",
	},
	"k": {
		ToKelvin:   func(x float64) float64 { return x },
		FromKelvin: func(x float64) float64 { return x },
		Name:       "Кельвин", Symbol: "K",
	},
	"ra": {
		ToKelvin:   func(x float64) float64 { return x * 5 / 9 },
		FromKelvin: func(x float64) float64 { return x * 9 / 5 },
		Name:       "Ранкин", Symbol: "°Ra",
	},
	"re": {
		ToKelvin:   func(x float64) float64 { return x*5/4 + 273.15 },
		FromKelvin: func(x float64) float64 { return (x - 273.15) * 4 / 5 },
		Name:       "Реомюр", Symbol: "°Ré",
	},
	"n": {
		ToKelvin:   func(x float64) float64 { return x*100/33 + 273.15 },
		FromKelvin: func(x float64) float64 { return (x - 273.15) * 33 / 100 },
		Name:       "Ньютон", Symbol: "°N",
	},
	"de": {
		ToKelvin:   func(x float64) float64 { return 373.15 - x*2/3 },
		FromKelvin: func(x float64) float64 { return (373.15 - x) * 3 / 2 },
		Name:       "Делиль", Symbol: "°De",
	},
	"ro": {
		ToKelvin:   func(x float64) float64 { return (x-7.5)*40/21 + 273.15 },
		FromKelvin: func(x float64) float64 { return (x-273.15)*21/40 + 7.5 },
		Name:       "Рёмер", Symbol: "°Rø",
	},
}

func convert(value float64, from, to string) (float64, error) {
	if from == to {
		return value, nil
	}
	f, ok := scales[from]
	if !ok {
		return 0, fmt.Errorf("неизвестная шкала: %s", from)
	}
	t, ok := scales[to]
	if !ok {
		return 0, fmt.Errorf("неизвестная шкала: %s", to)
	}
	kelvin := f.ToKelvin(value)
	return t.FromKelvin(kelvin), nil
}

func main() {
	var (
		value     float64
		from      string
		to        string
		precision int
		batch     string
		output    string
		list      bool
		rangeArgs string
	)
	flag.Float64Var(&value, "value", 0, "Значение для конвертации")
	flag.StringVar(&from, "from", "c", "Исходная шкала")
	flag.StringVar(&to, "to", "f", "Целевая шкала")
	flag.IntVar(&precision, "precision", 2, "Количество знаков после запятой")
	flag.StringVar(&batch, "batch", "", "Файл со значениями (по одному на строку)")
	flag.StringVar(&output, "output", "", "Файл для сохранения результатов")
	flag.BoolVar(&list, "list", false, "Показать список шкал")
	flag.StringVar(&rangeArgs, "range", "", "Диапазон для таблицы: start,end,step")
	flag.Parse()

	if list {
		fmt.Println("Доступные шкалы:")
		for key, s := range scales {
			fmt.Printf("  %s: %s (%s)\n", key, s.Name, s.Symbol)
		}
		return
	}

	if rangeArgs != "" {
		parts := strings.Split(rangeArgs, ",")
		if len(parts) != 3 {
			fmt.Println("Формат --range: start,end,step")
			return
		}
		start, _ := strconv.ParseFloat(parts[0], 64)
		end, _ := strconv.ParseFloat(parts[1], 64)
		step, _ := strconv.ParseFloat(parts[2], 64)
		if step <= 0 {
			fmt.Println("Шаг должен быть положительным")
			return
		}
		rows := []string{}
		for v := start; v <= end+1e-9; v += step {
			res, _ := convert(v, from, to)
			rows = append(rows, fmt.Sprintf("%.*f %s = %.*f %s",
				precision, v, scales[from].Symbol,
				precision, res, scales[to].Symbol))
		}
		if output != "" {
			os.WriteFile(output, []byte(strings.Join(rows, "\n")), 0644)
			fmt.Printf("Таблица сохранена в %s\n", output)
		} else {
			fmt.Printf("Таблица %s -> %s:\n", scales[from].Name, scales[to].Name)
			for _, row := range rows {
				fmt.Println(row)
			}
		}
		return
	}

	if batch != "" {
		file, err := os.Open(batch)
		if err != nil {
			fmt.Printf("Ошибка открытия %s: %v\n", batch, err)
			return
		}
		defer file.Close()
		scanner := bufio.NewScanner(file)
		values := []float64{}
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" {
				continue
			}
			v, err := strconv.ParseFloat(line, 64)
			if err != nil {
				fmt.Printf("Пропущено нечисловое значение: %s\n", line)
				continue
			}
			values = append(values, v)
		}
		results := []string{}
		for _, v := range values {
			res, _ := convert(v, from, to)
			results = append(results, fmt.Sprintf("%.*f -> %.*f", precision, v, precision, res))
		}
		if output != "" {
			os.WriteFile(output, []byte(strings.Join(results, "\n")), 0644)
			fmt.Printf("Результаты сохранены в %s\n", output)
		} else {
			for _, r := range results {
				fmt.Println(r)
			}
		}
		return
	}

	if flag.NFlag() == 0 {
		fmt.Println("Укажите --value или --batch или --range, или --list")
		return
	}

	res, err := convert(value, from, to)
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Printf("%.*f %s = %.*f %s\n", precision, value, scales[from].Symbol, precision, res, scales[to].Symbol)
}
