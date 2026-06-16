// temp_convert.rs - Конвертер температур на Rust (CLI)
// Зависимости: clap, colored
use clap::{Arg, App};
use colored::*;
use std::collections::HashMap;
use std::fs::File;
use std::io::{self, BufRead, Write};
use std::str::FromStr;

lazy_static::lazy_static! {
    static ref SCALES: HashMap<String, Scale> = {
        let mut m = HashMap::new();
        m.insert("c".to_string(), Scale {
            to_kelvin: |x| x + 273.15,
            from_kelvin: |x| x - 273.15,
            name: "Цельсий".to_string(),
            symbol: "°C".to_string(),
        });
        // ... аналогично остальным шкалам (сокращённо для примера)
        m
    };
}

struct Scale {
    to_kelvin: fn(f64) -> f64,
    from_kelvin: fn(f64) -> f64,
    name: String,
    symbol: String,
}

fn convert(value: f64, from: &str, to: &str) -> Result<f64, String> {
    if from == to { return Ok(value); }
    let f = SCALES.get(from).ok_or_else(|| format!("Неизвестная шкала: {}", from))?;
    let t = SCALES.get(to).ok_or_else(|| format!("Неизвестная шкала: {}", to))?;
    let kelvin = (f.to_kelvin)(value);
    Ok((t.from_kelvin)(kelvin))
}

fn main() {
    let matches = App::new("Temp Converter")
        .arg(Arg::with_name("value").short("v").long("value").takes_value(true).help("Значение"))
        .arg(Arg::with_name("from").short("f").long("from").default_value("c").help("Исходная шкала"))
        .arg(Arg::with_name("to").short("t").long("to").default_value("f").help("Целевая шкала"))
        .arg(Arg::with_name("precision").short("p").long("precision").default_value("2").help("Точность"))
        .arg(Arg::with_name("batch").short("b").long("batch").takes_value(true).help("Файл со значениями"))
        .arg(Arg::with_name("output").short("o").long("output").takes_value(true).help("Выходной файл"))
        .arg(Arg::with_name("list").long("list").help("Показать шкалы"))
        .arg(Arg::with_name("range").long("range").takes_value(true).help("start,end,step"))
        .get_matches();

    if matches.is_present("list") {
        println!("Доступные шкалы:");
        for (key, s) in SCALES.iter() {
            println!("  {}: {} ({})", key, s.name, s.symbol);
        }
        return;
    }

    let precision: usize = matches.value_of("precision").unwrap().parse().unwrap_or(2);
    let from = matches.value_of("from").unwrap();
    let to = matches.value_of("to").unwrap();

    if let Some(range) = matches.value_of("range") {
        let parts: Vec<&str> = range.split(',').collect();
        if parts.len() != 3 {
            eprintln!("Формат --range: start,end,step");
            return;
        }
        let start: f64 = parts[0].parse().unwrap();
        let end: f64 = parts[1].parse().unwrap();
        let step: f64 = parts[2].parse().unwrap();
        if step <= 0.0 { eprintln!("Шаг должен быть положительным"); return; }
        let mut rows = Vec::new();
        let mut v = start;
        while v <= end + 1e-9 {
            let res = convert(v, from, to).unwrap();
            rows.push(format!("{:.prec$} {} = {:.prec$} {}", v, SCALES[from].symbol, res, SCALES[to].symbol, prec=precision));
            v += step;
        }
        if let Some(out) = matches.value_of("output") {
            let content = rows.join("\n");
            std::fs::write(out, content).unwrap();
            println!("Таблица сохранена в {}", out);
        } else {
            println!("Таблица {} -> {}:", SCALES[from].name, SCALES[to].name);
            for row in rows { println!("{}", row); }
        }
        return;
    }

    if let Some(batch_file) = matches.value_of("batch") {
        let file = File::open(batch_file).expect("Не удалось открыть файл");
        let reader = io::BufReader::new(file);
        let mut results = Vec::new();
        for line in reader.lines() {
            let line = line.unwrap();
            if line.trim().is_empty() { continue; }
            let val: f64 = line.trim().parse().unwrap_or(0.0);
            let res = convert(val, from, to).unwrap();
            results.push(format!("{:.prec$} -> {:.prec$}", val, res, prec=precision));
        }
        if let Some(out) = matches.value_of("output") {
            std::fs::write(out, results.join("\n")).unwrap();
            println!("Результаты сохранены в {}", out);
        } else {
            for r in results { println!("{}", r); }
        }
        return;
    }

    if let Some(val_str) = matches.value_of("value") {
        let value: f64 = val_str.parse().unwrap();
        let res = convert(value, from, to).unwrap();
        println!("{:.prec$} {} = {:.prec$} {}", value, SCALES[from].symbol, res, SCALES[to].symbol, prec=precision);
    } else {
        eprintln!("Укажите --value, --batch, --range или --list");
    }
}
