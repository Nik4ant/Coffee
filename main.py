import sys
import os
import sqlite3

from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QDialog
from PyQt5 import uic
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtCore import QPoint, Qt

import main_form
import addEditCoffeeForm


class main_window(QWidget, main_form.Ui_Form):
    def closeEvent(self, event):
        # Закрываем соединение с БД
        self.connection.close()

    def __init__(self):
        # Конструктор QWidget
        super().__init__()

        # Загружаем UI
        self.setupUi(self)

        # Соединение с БД
        self.connection = sqlite3.connect("data/coffee.sqlite")

        self.init_ui()

    def init_ui(self):
        # Настраиваем таблицу
        self.table_widget_coffee.setColumnCount(7)
        self.table_widget_coffee.setHorizontalHeaderLabels(["Id", "Название сорта", "Степень обжарки",
                                                            "Молотый", "Описание вкуса", "Цена", "Объём"])

        # Компануем main_layout
        self.vlayout_main.addWidget(self.table_widget_coffee)
        self.setLayout(self.vlayout_main)

        # Выводим данные о кофе
        self.display_coffee_data()

        # Сигналы
        self.button_add.clicked.connect(self.open_add_edit_window)
        self.table_widget_coffee.cellDoubleClicked.connect(self.cell_on_click)

    def display_coffee_data(self):
        coffee_data = self.connection.cursor().execute("SELECT * FROM coffee").fetchall()
        self.table_widget_coffee.setRowCount(0)
        # Заполнение таблицы данными
        for i, coffee in enumerate(coffee_data):
            # Добавляем и заполняем строчку
            self.table_widget_coffee.insertRow(self.table_widget_coffee.rowCount())
            self.table_widget_coffee.setItem(i, 0, QTableWidgetItem(str(coffee[0])))
            self.table_widget_coffee.setItem(i, 1, QTableWidgetItem(str(coffee[1])))
            self.table_widget_coffee.setItem(i, 2, QTableWidgetItem(str(coffee[2])))
            self.table_widget_coffee.setItem(i, 3, QTableWidgetItem("Да" if bool(coffee[3]) else "Нет"))
            self.table_widget_coffee.setItem(i, 4, QTableWidgetItem(str(coffee[4])))
            self.table_widget_coffee.setItem(i, 5, QTableWidgetItem(str(coffee[5])))
            self.table_widget_coffee.setItem(i, 6, QTableWidgetItem(str(coffee[6])))

    def cell_on_click(self, row: int, col: int):
        is_grounded = self.table_widget_coffee.item(row, 3).text().lower() == "да"
        # Данные о выбранном кофе
        data = {
            "id": int(self.table_widget_coffee.item(row, 0).text()),
            "name": self.table_widget_coffee.item(row, 1).text(),
            "fired_level": self.table_widget_coffee.item(row, 2).text(),
            "is_grounded": is_grounded,
            "taste": self.table_widget_coffee.item(row, 4).text(),
            "price": float(self.table_widget_coffee.item(row, 5).text()),
            "size": float(self.table_widget_coffee.item(row, 6).text()),
        }
        self.open_add_edit_window(data)

    def open_add_edit_window(self, data_for_editing={}):
        # Запускаем окно с добавлением/редактированием кофе
        add_edit_window(self, data_for_editing).exec_()
        # Обновляем таблицу
        self.display_coffee_data()


class add_edit_window(QDialog, addEditCoffeeForm.Ui_Form):
    def __init__(self, sender, data_for_editing={}):
        """
        Init
        :param sender: Объект, вызвавший окно, нужно, для обращения к БД
        :param data_for_editing: Данные о изменяемом кофе, если пустые, то кофе создают
        """

        # Конструктор QWidget
        super().__init__()

        # Загружаем UI
        self.setupUi(self)

        self.data_for_editing = data_for_editing
        self.sender = sender
        self.init_ui()

    def init_ui(self):
        # Если окно открыто для редактирования, то выводим данные о кофе
        if self.data_for_editing:
            # Блокируем окно с добавлением
            self.tab_add.setEnabled(False)
            # Заполняем поля данными
            self.line_edit_id.setText(str(self.data_for_editing["id"]) + " (не редактируется)")
            self.line_edit_name_edit.setText(self.data_for_editing["name"])
            self.line_edit_fired_level_edit.setText(self.data_for_editing["fired_level"])
            self.check_box_is_grounded_edit.setChecked(self.data_for_editing["is_grounded"])
            self.line_edit_taste_description_edit.setText(self.data_for_editing["taste"])
            self.double_spin_box_price_edit.setValue(self.data_for_editing["price"])
            self.double_spin_box_size_edit.setValue(self.data_for_editing["size"])
            # Кнопка для сохранения изменений
            self.button_save_changes.clicked.connect(self.save_changes)
        else:
            # Блокируем окно редактирования
            self.tab_edit.setEnabled(False)

            self.button_add.clicked.connect(self.add_coffee)

        # Компановка всех layout'ов
        self.tab_add.setLayout(self.vlayout_add_main)
        self.setLayout(self.vlayout_main)

    def save_changes(self):
        # Обновляем все данные кроме id (он и не должен меняться)
        QUERY = """
                UPDATE coffee
                SET name = ?,
                roasting_level = ?,
                is_ground = ?,
                taste_desc = ?,
                price = ?,
                size = ?
                WHERE id = ?
                """
        self.sender.connection.cursor().execute(QUERY,
                                                (self.line_edit_name_edit.text(),
                                                 self.line_edit_fired_level_edit.text(),
                                                 self.check_box_is_grounded_edit.isChecked(),
                                                 self.line_edit_taste_description_edit.text(),
                                                 self.double_spin_box_price_edit.value(),
                                                 self.double_spin_box_size_edit.value(),
                                                 int(self.line_edit_id.text().split()[0]),))
        self.sender.connection.commit()
        self.close()

    def add_coffee(self):
        # Проверка, что параметры, корректные
        if (not self.line_edit_name_add.text().replace(' ', '') or
                not self.line_edit_fired_level_add.text().replace(' ', '') or
                not self.line_edit_taste_description_add.text().replace(' ', '')):
            return

        # Добавляем данные
        QUERY = """
                INSERT  INTO coffee (name, roasting_level, 
                is_ground, taste_desc, 
                price, size) VALUES(?, ?, ?, ?, ?, ?)
                """
        self.sender.connection.cursor().execute(QUERY,
                                                (self.line_edit_name_add.text(),
                                                 self.line_edit_fired_level_add.text(),
                                                 self.check_box_is_grounded_add.isChecked(),
                                                 self.line_edit_taste_description_add.text(),
                                                 self.double_spin_box_price_add.value(),
                                                 self.double_spin_box_size_add.value(),))
        self.sender.connection.commit()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = main_window()
    ex.show()
    sys.exit(app.exec_())