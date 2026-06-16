// TempConverter.cs - Конвертер температур на C# (CLI + WinForms)
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows.Forms;

namespace TempConverter
{
    public class Scale
    {
        public string Name { get; set; }
        public string Symbol { get; set; }
        public Func<double, double> ToKelvin { get; set; }
        public Func<double, double> FromKelvin { get; set; }
    }

    public static class Converter
    {
        public static Dictionary<string, Scale> Scales = new Dictionary<string, Scale>
        {
            {"c", new Scale{Name="Цельсий", Symbol="°C", ToKelvin=x=>x+273.15, FromKelvin=x=>x-273.15}},
            {"f", new Scale{Name="Фаренгейт", Symbol="°F", ToKelvin=x=>(x-32)*5/9+273.15, FromKelvin=x=>(x-273.15)*9/5+32}},
            {"k", new Scale{Name="Кельвин", Symbol="K", ToKelvin=x=>x, FromKelvin=x=>x}},
            {"ra", new Scale{Name="Ранкин", Symbol="°Ra", ToKelvin=x=>x*5/9, FromKelvin=x=>x*9/5}},
            {"re", new Scale{Name="Реомюр", Symbol="°Ré", ToKelvin=x=>x*5/4+273.15, FromKelvin=x=>(x-273.15)*4/5}},
            {"n", new Scale{Name="Ньютон", Symbol="°N", ToKelvin=x=>x*100/33+273.15, FromKelvin=>(x-273.15)*33/100}},
            {"de", new Scale{Name="Делиль", Symbol="°De", ToKelvin=x=>373.15-x*2/3, FromKelvin=>(373.15-x)*3/2}},
            {"ro", new Scale{Name="Рёмер", Symbol="°Rø", ToKelvin=x=>(x-7.5)*40/21+273.15, FromKelvin=>(x-273.15)*21/40+7.5}}
        };

        public static double Convert(double value, string from, string to)
        {
            if (from == to) return value;
            var f = Scales[from];
            var t = Scales[to];
            double kelvin = f.ToKelvin(value);
            return t.FromKelvin(kelvin);
        }

        public static List<double> ConvertBatch(List<double> values, string from, string to)
        {
            return values.Select(v => Convert(v, from, to)).ToList();
        }

        public static List<Tuple<string, string>> GenerateTable(double start, double end, double step, string from, string to, int precision)
        {
            var rows = new List<Tuple<string, string>>();
            for (double v = start; v <= end + 1e-9; v += step)
            {
                double res = Convert(v, from, to);
                rows.Add(Tuple.Create(
                    $"{v.ToString($"F{precision}")} {Scales[from].Symbol}",
                    $"{res.ToString($"F{precision}")} {Scales[to].Symbol}"
                ));
            }
            return rows;
        }

        public static void ListScales()
        {
            Console.WriteLine("Доступные шкалы:");
            foreach (var kv in Scales)
                Console.WriteLine($"  {kv.Key}: {kv.Value.Name} ({kv.Value.Symbol})");
        }
    }

    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            if (args.Length > 0 && args[0] == "--gui")
            {
                Application.EnableVisualStyles();
                Application.Run(new TempConverterGUI());
                return;
            }
            // CLI (упрощённый)
            var opts = new Dictionary<string, string>();
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i].StartsWith("--"))
                {
                    if (i + 1 < args.Length && !args[i + 1].StartsWith("--"))
                        opts[args[i]] = args[++i];
                    else
                        opts[args[i]] = "";
                }
            }
            try
            {
                if (opts.ContainsKey("--list"))
                {
                    Converter.ListScales();
                    return;
                }
                string from = opts.GetValueOrDefault("--from", "c");
                string to = opts.GetValueOrDefault("--to", "f");
                int precision = int.Parse(opts.GetValueOrDefault("--precision", "2"));
                if (opts.ContainsKey("--range"))
                {
                    var parts = opts["--range"].Split(',');
                    if (parts.Length != 3) throw new Exception("Формат: start,end,step");
                    double start = double.Parse(parts[0]);
                    double end = double.Parse(parts[1]);
                    double step = double.Parse(parts[2]);
                    if (step <= 0) throw new Exception("Шаг должен быть положительным");
                    var table = Converter.GenerateTable(start, end, step, from, to, precision);
                    if (opts.ContainsKey("--output"))
                    {
                        File.WriteAllLines(opts["--output"], table.Select(r => $"{r.Item1} = {r.Item2}"));
                        Console.WriteLine($"Таблица сохранена в {opts["--output"]}");
                    }
                    else
                    {
                        Console.WriteLine($"Таблица {Converter.Scales[from].Name} -> {Converter.Scales[to].Name}:");
                        foreach (var r in table) Console.WriteLine($"{r.Item1} = {r.Item2}");
                    }
                    return;
                }
                if (opts.ContainsKey("--batch"))
                {
                    var values = File.ReadAllLines(opts["--batch"]).Where(l => !string.IsNullOrWhiteSpace(l))
                                    .Select(l => double.Parse(l.Trim())).ToList();
                    var results = Converter.ConvertBatch(values, from, to);
                    if (opts.ContainsKey("--output"))
                    {
                        var lines = values.Select((v, i) => $"{v.ToString($"F{precision}")} -> {results[i].ToString($"F{precision}")}");
                        File.WriteAllLines(opts["--output"], lines);
                        Console.WriteLine($"Результаты сохранены в {opts["--output"]}");
                    }
                    else
                    {
                        for (int i = 0; i < values.Count; i++)
                            Console.WriteLine($"{values[i]:F{precision}} -> {results[i]:F{precision}}");
                    }
                    return;
                }
                if (opts.ContainsKey("--value"))
                {
                    double value = double.Parse(opts["--value"]);
                    double res = Converter.Convert(value, from, to);
                    Console.WriteLine($"{value:F{precision}} {Converter.Scales[from].Symbol} = {res:F{precision}} {Converter.Scales[to].Symbol}");
                }
                else
                {
                    Console.WriteLine("Укажите --value, --batch, --range, --list или --gui");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Ошибка: {ex.Message}");
            }
        }
    }

    // ========== GUI ==========
    public class TempConverterGUI : Form
    {
        private TextBox valueBox, resultBox;
        private ComboBox fromBox, toBox;
        private NumericUpDown precisionUpDown;

        public TempConverterGUI()
        {
            Text = "Конвертер температур";
            Size = new System.Drawing.Size(450, 300);
            StartPosition = FormStartPosition.CenterScreen;

            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 7, Padding = new Padding(10) };
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            layout.Controls.Add(new Label { Text = "Значение:", AutoSize = true }, 0, 0);
            valueBox = new TextBox();
            layout.Controls.Add(valueBox, 1, 0);

            layout.Controls.Add(new Label { Text = "Из:", AutoSize = true }, 0, 1);
            fromBox = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, DataSource = new BindingSource(Converter.Scales.Keys.ToList(), null) };
            fromBox.SelectedItem = "c";
            layout.Controls.Add(fromBox, 1, 1);

            layout.Controls.Add(new Label { Text = "В:", AutoSize = true }, 0, 2);
            toBox = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, DataSource = new BindingSource(Converter.Scales.Keys.ToList(), null) };
            toBox.SelectedItem = "f";
            layout.Controls.Add(toBox, 1, 2);

            layout.Controls.Add(new Label { Text = "Точность:", AutoSize = true }, 0, 3);
            precisionUpDown = new NumericUpDown { Minimum = 0, Maximum = 10, Value = 2 };
            layout.Controls.Add(precisionUpDown, 1, 3);

            var convertBtn = new Button { Text = "Конвертировать" };
            convertBtn.Click += (s, e) => Convert();
            layout.Controls.Add(convertBtn, 0, 4);
            layout.SetColumnSpan(convertBtn, 2);

            layout.Controls.Add(new Label { Text = "Результат:", AutoSize = true }, 0, 5);
            resultBox = new TextBox { ReadOnly = true };
            layout.Controls.Add(resultBox, 1, 5);

            var btnPanel = new FlowLayoutPanel();
            var reverseBtn = new Button { Text = "Обратный" };
            reverseBtn.Click += (s, e) => Reverse();
            btnPanel.Controls.Add(reverseBtn);
            var tableBtn = new Button { Text = "Таблица" };
            tableBtn.Click += (s, e) => ShowTable();
            btnPanel.Controls.Add(tableBtn);
            layout.Controls.Add(btnPanel, 0, 6);
            layout.SetColumnSpan(btnPanel, 2);

            Controls.Add(layout);
        }

        private void Convert()
        {
            try
            {
                double val = double.Parse(valueBox.Text);
                string from = fromBox.SelectedItem.ToString();
                string to = toBox.SelectedItem.ToString();
                int prec = (int)precisionUpDown.Value;
                double res = Converter.Convert(val, from, to);
                resultBox.Text = $"{res.ToString($"F{prec}")} {Converter.Scales[to].Symbol}";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка: {ex.Message}");
            }
        }

        private void Reverse()
        {
            object from = fromBox.SelectedItem;
            object to = toBox.SelectedItem;
            fromBox.SelectedItem = to;
            toBox.SelectedItem = from;
            if (!string.IsNullOrEmpty(resultBox.Text)) Convert();
        }

        private void ShowTable()
        {
            try
            {
                double val = double.Parse(valueBox.Text);
                double start = val - 10, end = val + 10, step = 1.0;
                int prec = (int)precisionUpDown.Value;
                string from = fromBox.SelectedItem.ToString();
                string to = toBox.SelectedItem.ToString();
                var table = Converter.GenerateTable(start, end, step, from, to, prec);
                var sb = new System.Text.StringBuilder();
                sb.AppendLine($"{Converter.Scales[from].Name} -> {Converter.Scales[to].Name}:");
                foreach (var r in table)
                    sb.AppendLine($"{r.Item1} = {r.Item2}");
                MessageBox.Show(sb.ToString(), "Таблица", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка: {ex.Message}");
            }
        }
    }
}
