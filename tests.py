import sys
import unittest
from pathlib import Path

from PyQt5.Qt import QApplication

from main import PDFMaker

app = QApplication(sys.argv)


class PDFMakerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.form = PDFMaker()
        self.form.testingMode = True

    def test_are_chosen_files_empty_on_start(self):
        assert self.form.chosenFiles == []

    def test_are_items_in_chosen_files_paths(self):
        self.form.chooseFilesHandler()
        assert all(isinstance(x, Path) for x in self.form.chosenFiles)

    def test_are_items_in_correct_order_after_moving_down(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[2:4], down_direction=True)
        itemsAfter = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        desired = ['test1.png', 'test2.png', 'test5.png', 'test3.png', 'test4.png', 'test6.png', 'test7.png', ]
        assert all(x.text() == y for x, y in zip(itemsAfter, desired))

    def test_are_items_in_correct_order_after_moving_to_bottom(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[1:5], down_direction=True, to_edge=True)
        itemsAfter = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        desired = ['test1.png', 'test6.png', 'test7.png', 'test2.png', 'test3.png', 'test4.png', 'test5.png', ]
        assert all(x.text() == y for x, y in zip(itemsAfter, desired))

    def test_are_items_in_correct_order_after_moving_up(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[3:5], down_direction=False)
        itemsAfter = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        desired = ['test1.png', 'test2.png', 'test4.png', 'test5.png', 'test3.png', 'test6.png', 'test7.png', ]
        assert all(x.text() == y for x, y in zip(itemsAfter, desired))

    def test_are_items_in_correct_order_after_moving_to_top(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[5:], down_direction=False, to_edge=True)
        itemsAfter = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        desired = ['test6.png', 'test7.png', 'test1.png', 'test2.png', 'test3.png', 'test4.png', 'test5.png', ]
        assert all(x.text() == y for x, y in zip(itemsAfter, desired))

    def test_not_moving_up_items_if_already_at_top(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[0:2], down_direction=False)
        itemsAfter = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        assert allItems == itemsAfter

    def test_not_moving_down_items_if_already_at_bottom(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[5:], down_direction=True)
        itemsAfter = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        assert allItems == itemsAfter

    def test_are_chosen_files_in_correct_order(self):
        self.form.chooseFilesHandler()
        allItems = [self.form.filesList.item(i) for i in range(0, self.form.filesList.count())]
        self.form.moveItem(allItems[2:5], down_direction=False)
        self.form.moveItem(allItems[0:1], down_direction=True, to_edge=True)
        self.form.orderFiles()
        desired = ['test3.png', 'test4.png', 'test5.png', 'test2.png', 'test6.png', 'test7.png', 'test1.png', ]
        assert all(x.name == y for x, y in zip(self.form.chosenFiles, desired))

    def test_are_added_items_in_list(self):
        self.form.chooseFilesHandler()
        self.form.addItem()
        desired = ['test1.png', 'test2.png', 'test3.png', 'test4.png', 'test5.png', 'test6.png', 'test7.png', ] * 2
        assert all(x.name == y for x, y in zip(self.form.chosenFiles, desired))
