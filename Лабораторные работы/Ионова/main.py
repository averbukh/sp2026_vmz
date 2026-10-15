import math
import matplotlib.pyplot as plt

def get_float_input(prompt):
    """Вспомогательная функция для безопасного ввода чисел"""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Ошибка! Пожалуйста, введите число (можно с точкой, например 1.5).")

def main():
    print("="*40)
    print(" ПРОГРАММА РАСЧЕТА ФУНКЦИИ y(x)")
    print("="*40)
    
    # 1. Ввод данных
    print("\nВведите коэффициенты a:")
    a1 = get_float_input("a1 = ")
    a2 = get_float_input("a2 = ")
    a3 = get_float_input("a3 = ")
    
    print("\nВведите частоты b:")
    b1 = get_float_input("b1 = ")
    b2 = get_float_input("b2 = ")
    b3 = get_float_input("b3 = ")
    
    print("\nВведите диапазон изменения x:")
    x0 = get_float_input("Начальное значение x0 = ")
    xk = get_float_input("Конечное значение xk = ")
    dx = get_float_input("Шаг dx = ")

    if dx <= 0:
        print("Ошибка: Шаг dx должен быть больше нуля!")
        return

    # 2. Расчет значений
    x_values = []
    y_values = []
    
    # Рассчитываем количество шагов
    steps = int((xk - x0) / dx) + 1
    
    print("\n" + "="*40)
    print(f"{'№':^5} | {'x':^12} | {'y(x)':^12}")
    print("-" * 40)
    
    for i in range(steps):
        x = x0 + i * dx
        # Формула из задания
        y = a1 * math.sin(b1 * x) + a2 * math.sin(b2 * x) + a3 * math.sin(b3 * x)
        
        x_values.append(x)
        y_values.append(y)
        
        # Вывод строки таблицы
        print(f"{i+1:^5} | {x:^12.4f} | {y:^12.4f}")
        
    print("="*40)

    # 3. Построение графика
    plt.figure(figsize=(10, 6))
    plt.plot(x_values, y_values, marker='o', markersize=3, linestyle='-', color='b', label='y(x)')
    
    plt.title('График функции y(x) = a1*sin(b1*x) + a2*sin(b2*x) + a3*sin(b3*x)')
    plt.xlabel('Ось X')
    plt.ylabel('Ось Y')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Сохранение графика в файл (как требует задание)
    filename = "graphic.svg"
    plt.savefig(filename)
    print(f"\n[УСПЕХ] График сохранен в файл: {filename}")
    
    # Отображение графика на экране
    print("Открытие окна с графиком...")
    plt.show()

if __name__ == "__main__":
    main()