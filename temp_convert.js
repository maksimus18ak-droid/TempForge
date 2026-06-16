// temp_convert.js - Конвертер температур на JavaScript (Node.js CLI + веб)
// Для Node.js: используйте commander
// Для браузера: вставьте код в HTML

// ========== ШКАЛЫ ==========
const SCALES = {
    c: { toKelvin: x => x + 273.15, fromKelvin: x => x - 273.15, name: 'Цельсий', symbol: '°C' },
    f: { toKelvin: x => (x - 32) * 5/9 + 273.15, fromKelvin: x => (x - 273.15) * 9/5 + 32, name: 'Фаренгейт', symbol: '°F' },
    k: { toKelvin: x => x, fromKelvin: x => x, name: 'Кельвин', symbol: 'K' },
    ra: { toKelvin: x => x * 5/9, fromKelvin: x => x * 9/5, name: 'Ранкин', symbol: '°Ra' },
    re: { toKelvin: x => x * 5/4 + 273.15, fromKelvin: x => (x - 273.15) * 4/5, name: 'Реомюр', symbol: '°Ré' },
    n: { toKelvin: x => x * 100/33 + 273.15, fromKelvin: x => (x - 273.15) * 33/100, name: 'Ньютон', symbol: '°N' },
    de: { toKelvin: x => 373.15 - x * 2/3, fromKelvin: x => (373.15 - x) * 3/2, name: 'Делиль', symbol: '°De' },
    ro: { toKelvin: x => (x - 7.5) * 40/21 + 273.15, fromKelvin: x => (x - 273.15) * 21/40 + 7.5, name: 'Рёмер', symbol: '°Rø' },
};

// ========== ОСНОВНАЯ ЛОГИКА ==========
class TemperatureConverter {
    static convert(value, fromScale, toScale) {
        if (fromScale === toScale) return value;
        if (!SCALES[fromScale] || !SCALES[toScale]) throw new Error('Неизвестная шкала');
        const kelvin = SCALES[fromScale].toKelvin(value);
        return SCALES[toScale].fromKelvin(kelvin);
    }

    static convertBatch(values, fromScale, toScale) {
        return values.map(v => this.convert(v, fromScale, toScale));
    }

    static getScaleInfo(scale) {
        if (!SCALES[scale]) throw new Error('Неизвестная шкала');
        return SCALES[scale];
    }

    static listScales() {
        return Object.keys(SCALES);
    }
}

// ========== CLI (Node.js) ==========
if (typeof require !== 'undefined' && require.main === module) {
    const fs = require('fs');
    const { program } = require('commander');

    program
        .option('-v, --value <number>', 'Значение для конвертации', parseFloat)
        .option('-f, --from <scale>', 'Исходная шкала', 'c')
        .option('-t, --to <scale>', 'Целевая шкала', 'f')
        .option('-p, --precision <number>', 'Количество знаков после запятой', parseInt, 2)
        .option('-b, --batch <file>', 'Файл со значениями (по одному на строку)')
        .option('-o, --output <file>', 'Файл для сохранения результатов')
        .option('--range <start> <end> <step>', 'Диапазон для таблицы', (s, e, st) => [parseFloat(s), parseFloat(e), parseFloat(st)])
        .option('--list', 'Показать список шкал')
        .parse(process.argv);

    const opts = program.opts();

    if (opts.list) {
        console.log('Доступные шкалы:');
        for (const key of TemperatureConverter.listScales()) {
            const info = TemperatureConverter.getScaleInfo(key);
            console.log(`  ${key}: ${info.name} (${info.symbol})`);
        }
        process.exit(0);
    }

    function formatTemp(value, scale, precision) {
        const info = TemperatureConverter.getScaleInfo(scale);
        return `${value.toFixed(precision)} ${info.symbol}`;
    }

    if (opts.range) {
        const [start, end, step] = opts.range;
        if (step <= 0) {
            console.error('Шаг должен быть положительным');
            process.exit(1);
        }
        const rows = [];
        for (let v = start; v <= end + 1e-9; v += step) {
            const conv = TemperatureConverter.convert(v, opts.from, opts.to);
            rows.push(`${formatTemp(v, opts.from, opts.precision)} = ${formatTemp(conv, opts.to, opts.precision)}`);
        }
        if (opts.output) {
            fs.writeFileSync(opts.output, rows.join('\n'), 'utf8');
            console.log(`Таблица сохранена в ${opts.output}`);
        } else {
            console.log(`Таблица ${TemperatureConverter.getScaleInfo(opts.from).name} -> ${TemperatureConverter.getScaleInfo(opts.to).name}:`);
            rows.forEach(r => console.log(r));
        }
        process.exit(0);
    }

    if (opts.batch) {
        const data = fs.readFileSync(opts.batch, 'utf8');
        const values = data.split('\n').filter(l => l.trim()).map(Number);
        const results = TemperatureConverter.convertBatch(values, opts.from, opts.to);
        if (opts.output) {
            const lines = values.map((v, i) => `${v} -> ${results[i]}`);
            fs.writeFileSync(opts.output, lines.join('\n'), 'utf8');
            console.log(`Результаты сохранены в ${opts.output}`);
        } else {
            values.forEach((v, i) => console.log(`${v} -> ${results[i].toFixed(opts.precision)}`));
        }
        process.exit(0);
    }

    if (opts.value !== undefined) {
        const result = TemperatureConverter.convert(opts.value, opts.from, opts.to);
        console.log(`${formatTemp(opts.value, opts.from, opts.precision)} = ${formatTemp(result, opts.to, opts.precision)}`);
    } else {
        console.log('Укажите --value или --batch или --range');
    }
}

// ========== Браузерная версия ==========
if (typeof window !== 'undefined') {
    window.TemperatureConverter = TemperatureConverter;
    window.SCALES = SCALES;
    window.convertTemp = function(value, from, to, precision = 2) {
        try {
            const result = TemperatureConverter.convert(value, from, to);
            return { value: result, formatted: `${result.toFixed(precision)} ${SCALES[to].symbol}` };
        } catch (e) {
            return { error: e.message };
        }
    };
}
