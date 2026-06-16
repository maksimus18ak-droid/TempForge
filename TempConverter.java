// TempConverter.java - Конвертер температур на Java (CLI + Swing GUI)
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import java.util.function.DoubleUnaryOperator;

public class TempConverter {
    // ========== ШКАЛЫ ==========
    private static final Map<String, Scale> SCALES = new LinkedHashMap<>();
    static {
        SCALES.put("c", new Scale("Цельсий", "°C", x -> x + 273.15, x -> x - 273.15));
        SCALES.put("f", new Scale("Фаренгейт", "°F", x -> (x - 32) * 5/9 + 273.15, x -> (x - 273.15) * 9/5 + 32));
        SCALES.put("k", new Scale("Кельвин", "K", x -> x, x -> x));
        SCALES.put("ra", new Scale("Ранкин", "°Ra", x -> x * 5/9, x -> x * 9/5));
        SCALES.put("re", new Scale("Реомюр", "°Ré", x -> x * 5/4 + 273.15, x -> (x - 273.15) * 4/5));
        SCALES.put("n", new Scale("Ньютон", "°N", x -> x * 100/33 + 273.15, x -> (x - 273.15) * 33/100));
        SCALES.put("de", new Scale("Делиль", "°De", x -> 373.15 - x * 2/3, x -> (373.15 - x) * 3/2));
        SCALES.put("ro", new Scale("Рёмер", "°Rø", x -> (x - 7.5) * 40/21 + 273.15, x -> (x - 273.15) * 21/40 + 7.5));
    }

    static class Scale {
        String name, symbol;
        DoubleUnaryOperator toKelvin, fromKelvin;
        Scale(String name, String symbol, DoubleUnaryOperator toK, DoubleUnaryOperator fromK) {
            this.name = name; this.symbol = symbol; this.toKelvin = toK; this.fromKelvin = fromK;
        }
    }

    public static double convert(double value, String from, String to) {
        if (from.equals(to)) return value;
        Scale f = SCALES.get(from), t = SCALES.get(to);
        if (f == null || t == null) throw new IllegalArgumentException("Неизвестная шкала");
        double kelvin = f.toKelvin.applyAsDouble(value);
        return t.fromKelvin.applyAsDouble(kelvin);
    }

    public static List<Double> convertBatch(List<Double> values, String from, String to) {
        List<Double> res = new ArrayList<>();
        for (double v : values) res.add(convert(v, from, to));
        return res;
    }

    public static List<String[]> generateTable(double start, double end, double step, String from, String to, int precision) {
        List<String[]> rows = new ArrayList<>();
        for (double v = start; v <= end + 1e-9; v += step) {
            double res = convert(v, from, to);
            rows.add(new String[]{
                String.format("%." + precision + "f %s", v, SCALES.get(from).symbol),
                String.format("%." + precision + "f %s", res, SCALES.get(to).symbol)
            });
        }
        return rows;
    }

    // ========== CLI ==========
    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("--gui")) {
            SwingUtilities.invokeLater(() -> new TempConverterGUI().setVisible(true));
            return;
        }
        // CLI парсинг упрощённый
        String from = "c", to = "f", batch = null, output = null, range = null;
        Double value = null;
        int precision = 2;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--value": value = Double.parseDouble(args[++i]); break;
                case "--from": from = args[++i]; break;
                case "--to": to = args[++i]; break;
                case "--precision": precision = Integer.parseInt(args[++i]); break;
                case "--batch": batch = args[++i]; break;
                case "--output": output = args[++i]; break;
                case "--range": range = args[++i]; break;
                case "--list": listScales(); return;
            }
        }
        try {
            if (range != null) {
                String[] parts = range.split(",");
                if (parts.length != 3) { System.err.println("Формат: start,end,step"); return; }
                double start = Double.parseDouble(parts[0]), end = Double.parseDouble(parts[1]), step = Double.parseDouble(parts[2]);
                if (step <= 0) { System.err.println("Шаг должен быть положительным"); return; }
                List<String[]> table = generateTable(start, end, step, from, to, precision);
                if (output != null) {
                    try (PrintWriter pw = new PrintWriter(output)) {
                        for (String[] row : table) pw.println(row[0] + " = " + row[1]);
                    }
                    System.out.println("Таблица сохранена в " + output);
                } else {
                    System.out.println("Таблица " + SCALES.get(from).name + " -> " + SCALES.get(to).name + ":");
                    for (String[] row : table) System.out.println(row[0] + " = " + row[1]);
                }
                return;
            }
            if (batch != null) {
                List<Double> values = new ArrayList<>();
                try (BufferedReader br = new BufferedReader(new FileReader(batch))) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        line = line.trim();
                        if (!line.isEmpty()) values.add(Double.parseDouble(line));
                    }
                }
                List<Double> results = convertBatch(values, from, to);
                if (output != null) {
                    try (PrintWriter pw = new PrintWriter(output)) {
                        for (int i = 0; i < values.size(); i++) {
                            pw.printf("%." + precision + "f -> %." + precision + "f\n", values.get(i), results.get(i));
                        }
                    }
                    System.out.println("Результаты сохранены в " + output);
                } else {
                    for (int i = 0; i < values.size(); i++) {
                        System.out.printf("%." + precision + "f -> %." + precision + "f\n", values.get(i), results.get(i));
                    }
                }
                return;
            }
            if (value != null) {
                double res = convert(value, from, to);
                System.out.printf("%." + precision + "f %s = %." + precision + "f %s\n", value, SCALES.get(from).symbol, res, SCALES.get(to).symbol);
            } else {
                System.out.println("Укажите --value, --batch, --range или --list");
            }
        } catch (Exception e) {
            System.err.println("Ошибка: " + e.getMessage());
        }
    }

    static void listScales() {
        System.out.println("Доступные шкалы:");
        for (Map.Entry<String, Scale> e : SCALES.entrySet()) {
            System.out.printf("  %s: %s (%s)\n", e.getKey(), e.getValue().name, e.getValue().symbol);
        }
    }

    // ========== GUI ==========
    static class TempConverterGUI extends JFrame {
        private JTextField valueField, resultField;
        private JComboBox<String> fromBox, toBox;
        private JSpinner precisionSpinner;

        public TempConverterGUI() {
            setTitle("Конвертер температур");
            setSize(450, 300);
            setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            setLayout(new GridBagLayout());
            GridBagConstraints gbc = new GridBagConstraints();
            gbc.insets = new Insets(5, 5, 5, 5);
            gbc.fill = GridBagConstraints.HORIZONTAL;

            gbc.gridx = 0; gbc.gridy = 0;
            add(new JLabel("Значение:"), gbc);
            gbc.gridx = 1;
            valueField = new JTextField(10);
            add(valueField, gbc);

            gbc.gridx = 0; gbc.gridy = 1;
            add(new JLabel("Из:"), gbc);
            gbc.gridx = 1;
            fromBox = new JComboBox<>(SCALES.keySet().toArray(new String[0]));
            fromBox.setSelectedItem("c");
            add(fromBox, gbc);

            gbc.gridx = 0; gbc.gridy = 2;
            add(new JLabel("В:"), gbc);
            gbc.gridx = 1;
            toBox = new JComboBox<>(SCALES.keySet().toArray(new String[0]));
            toBox.setSelectedItem("f");
            add(toBox, gbc);

            gbc.gridx = 0; gbc.gridy = 3;
            add(new JLabel("Точность:"), gbc);
            gbc.gridx = 1;
            precisionSpinner = new JSpinner(new SpinnerNumberModel(2, 0, 10, 1));
            add(precisionSpinner, gbc);

            JButton convertBtn = new JButton("Конвертировать");
            convertBtn.addActionListener(e -> convert());
            gbc.gridx = 0; gbc.gridy = 4; gbc.gridwidth = 2;
            add(convertBtn, gbc);

            gbc.gridy = 5;
            add(new JLabel("Результат:"), gbc);
            gbc.gridx = 1;
            resultField = new JTextField(15);
            resultField.setEditable(false);
            add(resultField, gbc);

            JPanel btnPanel = new JPanel(new FlowLayout());
            JButton reverseBtn = new JButton("Обратный");
            reverseBtn.addActionListener(e -> reverse());
            btnPanel.add(reverseBtn);
            JButton tableBtn = new JButton("Таблица");
            tableBtn.addActionListener(e -> showTable());
            btnPanel.add(tableBtn);
            gbc.gridy = 6; gbc.gridx = 0; gbc.gridwidth = 2;
            add(btnPanel, gbc);
        }

        private void convert() {
            try {
                double val = Double.parseDouble(valueField.getText());
                String from = (String) fromBox.getSelectedItem();
                String to = (String) toBox.getSelectedItem();
                int prec = (Integer) precisionSpinner.getValue();
                double res = TempConverter.convert(val, from, to);
                resultField.setText(String.format("%." + prec + "f %s", res, SCALES.get(to).symbol));
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Ошибка: " + ex.getMessage());
            }
        }

        private void reverse() {
            Object from = fromBox.getSelectedItem();
            Object to = toBox.getSelectedItem();
            fromBox.setSelectedItem(to);
            toBox.setSelectedItem(from);
            if (!resultField.getText().isEmpty()) convert();
        }

        private void showTable() {
            // Упрощённо: открыть диалог с таблицей
            try {
                double val = Double.parseDouble(valueField.getText());
                double start = val - 10, end = val + 10, step = 1.0;
                int prec = (Integer) precisionSpinner.getValue();
                String from = (String) fromBox.getSelectedItem();
                String to = (String) toBox.getSelectedItem();
                List<String[]> table = TempConverter.generateTable(start, end, step, from, to, prec);
                StringBuilder sb = new StringBuilder();
                sb.append(SCALES.get(from).name).append(" -> ").append(SCALES.get(to).name).append("\n");
                for (String[] row : table) sb.append(row[0]).append(" = ").append(row[1]).append("\n");
                JTextArea area = new JTextArea(sb.toString(), 15, 40);
                area.setEditable(false);
                JOptionPane.showMessageDialog(this, new JScrollPane(area), "Таблица", JOptionPane.PLAIN_MESSAGE);
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Ошибка: " + ex.getMessage());
            }
        }
    }
}
