import json
import matplotlib

import numexpr as ne
import numpy as np

from functools import partial
from tkinter import *
from tkinter.filedialog import asksaveasfile
from tkinter.filedialog import askopenfile

from matplotlib import pyplot as plt

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

matplotlib.use('TkAgg')


# class for entries storage (класс для хранения текстовых полей)
class Entries:
    def __init__(self):
        self.entries_list = []
        self.parent_window = None
        self.current = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    # adding of new entry (добавление нового текстового поля)
    def add_entry(self):
        new_entry = Entry(self.parent_window)
        new_entry.icursor(0)
        new_entry.focus()
        new_entry.pack()
        plot_button = self.parent_window.get_button_by_name('plot')
        if plot_button:
            plot_button.pack_forget()
        self.parent_window.add_button('plot', 'Plot', 'plot', hot_key='<Return>')
        self.entries_list.append(new_entry)

    def remove_entry(self, entry):
        """Removes an entry from entries list"""
        self.entries_list.remove(entry)
        entry.destroy()

    def remove_all_entries(self):
        """Removes all entries"""
        for entry in self.entries_list:
            entry.destroy()
        self.entries_list = []

    # удаление активного текстового поля и соответствующего графика
    def remove_current(self):
        """When the current entry is specified removes it"""
        self.remove_entry(self.current)
        self.current = None
        self.parent_window.commands.plot()

    def modal_for_entry_removal(self):
        """A prompt for entry removal. Creates a modal window which removes
        an entry if 'Yes' is chosen"""
        modal = ModalWindow(
            self,
            self.parent_window,
            title='Удаление: текстовое поле',
            labeltext='Нажмите \'Да\', если действительно хотите удалить текстовое поле, иначе нажмите \'Нет\''
        )
        confirm = Button(master=modal.top, text='Да', bg="green", fg="white", command=modal.delete)
        deny = Button(master=modal.top, text='Нет', bg="red", fg="white", command=modal.cancel)
        modal.add_button(deny)
        modal.add_button(confirm)
        return modal

    def delete_current(self):
        """Effectively deletes current entry and asks the user if the deletion is intentional"""
        if len(self.entries_list) >= 2:  # changed from 0 so that there is always 1 entry
            self.current = self.parent_window.focus_get()
            if self.current.get() != "":
                self.modal_for_entry_removal()
            else:
                self.remove_current()


# class for plotting (класс для построения графиков)
class Plotter:
    def __init__(self, x_min=-20, x_max=20, dx=0.01):
        self.x_min = x_min
        self.x_max = x_max
        self.dx = dx
        self._last_plotted_list_of_function = None
        self._last_plotted_figure = None
        self.parent_window = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    # plotting of graphics (построение графиков функций)
    def plot(self, list_of_function, title='Графики функций', x_label='x', y_label='y', need_legend=True):
        fig = plt.figure()

        x = np.arange(self.x_min, self.x_max, self.dx)

        new_funcs = [f if 'x' in f else 'x/x * ({})'.format(f) for f in list_of_function]

        ax = fig.add_subplot(1, 1, 1)
        for func in new_funcs:
            ax.plot(x, ne.evaluate(func), linewidth=1.5)

        fig.suptitle(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        if need_legend:
            plt.legend(list_of_function)
        self._last_plotted_list_of_function = list_of_function
        self._last_plotted_figure = fig
        return fig


# class for commands storage (класс для хранения команд)
class Commands:
    class State:
        def __init__(self):
            self.list_of_function = []

        def save_state(self):
            tmp_dict = {'list_of_function': self.list_of_function}
            file_out = asksaveasfile(defaultextension=".json")
            if file_out is not None:
                json.dump(tmp_dict, file_out)
            return self

        def reset_state(self):
            self.list_of_function = []

    def download(self):
        """Method for retrieving function names from a file specified in a prompt"""
        self.parent_window.entries.remove_all_entries()
        funcs = StringsFromFile(".json", 'functions').to_list()
        if funcs != []:
            for func_str in funcs:
                self.parent_window.entries.add_entry()
                self.parent_window.entries.entries_list[-1].insert(0, func_str)
            self.parent_window.commands.plot()
        return self

    def __init__(self, commands_dict=None):
        self.command_dict = commands_dict or {}
        self.__figure_canvas = None
        self.__navigation_toolbar = None
        self._state = Commands.State()
        self.__empty_entry_counter = 0
        self.parent_window = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    def add_command(self, name, command):
        self.command_dict[name] = command

    def add_all_commands(self, commands):
        """Adds all commands from a dict"""
        for name in commands:
            self.command_dict[name] = commands[name]
        return self

    def get_command_by_name(self, command_name):
        return self.command_dict[command_name]

    def __forget_canvas(self):
        if self.__figure_canvas is not None:
            self.__figure_canvas.get_tk_widget().pack_forget()

    def __forget_navigation(self):
        if self.__navigation_toolbar is not None:
            self.__navigation_toolbar.pack_forget()

    def plot(self, *args, **kwargs):
        def is_not_blank(s):
            return bool(s and not s.isspace())

        self._state.reset_state()
        list_of_function = []
        for entry in self.parent_window.entries.entries_list:
            get_func_str = entry.get()
            self._state.list_of_function.append(get_func_str)
            if is_not_blank(get_func_str):
                list_of_function.append(get_func_str)
            else:
                if self.__empty_entry_counter == 0:
                    mw = ModalWindow(
                        self,
                        self.parent_window,
                        title='Пустая строка',
                        labeltext='Это пример модального окна, возникающий, '
                                  'если ты ввел  пустую строку. С этим ничего '
                                  'делать не нужно. Просто нажми OK :)'
                    )
                    ok_button = Button(master=mw.top, text='OK', command=mw.cancel)
                    mw.add_button(ok_button)
                    self.__empty_entry_counter = 1
        self.__empty_entry_counter = 0
        figure = self.parent_window.plotter.plot(list_of_function)
        self._state.figure = figure
        self.__forget_canvas()
        self.__figure_canvas = FigureCanvasTkAgg(figure, self.parent_window)
        self.__forget_navigation()
        self.__navigation_toolbar = NavigationToolbar2Tk(self.__figure_canvas, self.parent_window)
        self.__figure_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        plot_button = self.parent_window.get_button_by_name('plot')
        if plot_button:
            plot_button.pack_forget()

    def add_func(self, *args, **kwargs):
        self.__forget_canvas()
        self.__forget_navigation()
        self.parent_window.entries.add_entry()

    def save_as(self):
        self._state.save_state()
        return self

    def delete_current(self, *args, **kwargs):
        """Forwards the delete call to parent window"""
        self.parent_window.entries.delete_current()
        return self


class StringsFromFile:
    def __init__(self, ext, prop):
        self.ext = ext
        self.prop = prop

    def to_list(self):
        """Retrieves an array of strings by a specific name from a file with a file prompt"""
        file = askopenfile(defaultextension=self.ext)
        if file is not None:
            data = json.load(file)
            return data[self.prop]
        return []


# class for buttons storage (класс для хранения кнопок)
class Buttons:
    def __init__(self):
        self.buttons = {}
        self.parent_window = None

    def set_parent_window(self, parent_window):
        self.parent_window = parent_window

    def add_button(self, name, text, command):
        new_button = Button(master=self.parent_window, text=text, command=command)
        self.buttons[name] = new_button
        return new_button

    def delete_button(self, name):
        button = self.buttons.get(name)
        if button:
            button.pack_forget()


# class for generate modal windows (класс для генерации модальных окон)
class ModalWindow:
    def __init__(self, window, parent, title, labeltext=''):
        self.buttons = []
        self.top = Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.window = window
        if len(title) > 0:
            self.top.title(title)
        if len(labeltext) == 0:
            labeltext = 'Default text'
        Label(self.top, text=labeltext).pack()

    def add_button(self, button):
        self.buttons.append(button)
        button.pack(pady=5)

    def cancel(self):
        self.top.destroy()

    def delete(self):
        """Removes an active text window"""
        self.window.remove_current()
        self.top.destroy()


# app class (класс приложения)
class App(Tk):
    def __init__(self, buttons, plotter, commands, entries):
        super().__init__()
        self.buttons = buttons
        self.plotter = plotter
        self.commands = commands
        self.entries = entries
        self.entries.set_parent_window(self)
        self.plotter.set_parent_window(self)
        self.commands.set_parent_window(self)
        self.buttons.set_parent_window(self)

    def add_button(self, name, text, command_name, *args, **kwargs):
        hot_key = kwargs.get('hot_key')
        if hot_key:
            kwargs.pop('hot_key')
        callback = partial(self.commands.get_command_by_name(command_name), *args, **kwargs)
        new_button = self.buttons.add_button(name=name, text=text, command=callback)
        if hot_key:
            self.bind(hot_key, callback)
        new_button.pack(fill=BOTH)

    def get_button_by_name(self, name):
        return self.buttons.buttons.get(name)

    def create_menu(self):
        menu = Menu(self)
        self.config(menu=menu)

        file_menu = Menu(menu)
        file_menu.add_command(label="Save as...", command=self.commands.get_command_by_name('save_as'))
        file_menu.add_command(label="Download", command=self.commands.get_command_by_name('download'))
        menu.add_cascade(label="File", menu=file_menu)


if __name__ == "__main__":
    commands = Commands()
    # init entries (создаем текстовые поля)
    entries_main = Entries()
    # init app (создаем экземпляр приложения)
    app = App(
        Buttons(),
        Plotter(),
        commands.add_all_commands(
            {
                'plot': commands.plot,
                'add_func': commands.add_func,
                'save_as': commands.save_as,
                'delete_current': commands.delete_current,
                'download': commands.download
            }
        ),
        entries_main
    )
    # init add func button (добавляем кнопку добавления новой функции)
    app.add_button('add_func', 'Добавить функцию', 'add_func', hot_key='<Control-a>')
    app.add_button('delete_current', 'Удалить поле', 'delete_current', hot_key='<Control-r>')
    # init first entry (создаем первое поле ввода)
    entries_main.add_entry()
    app.create_menu()
    # добавил комментарий для коммита
    # application launch (запуск "вечного" цикла приложеня)
    app.mainloop()
