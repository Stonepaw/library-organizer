﻿import clr
clr.AddReference("System.IO")
from System.IO import DirectoryInfo, Path, File, FileInfo
import unittest
import bookmover
from bookmover import BookMover, MoveResult, BookToMove, DuplicateHandler
from ComicRack import ComicRack
clr.AddReference('ComicRack.Engine')
from cYo.Projects.ComicRack.Engine import ComicBook  # @UnresolvedImport
from locommon import Mode
from losettings import Profile
from movereporter import MoveReporter
import i18n
clr.AddReference("NLog.dll")
from NLog import LogManager

log = LogManager.GetLogger("BookMoverTests")
# TODO: Tests to make:
# process_books
# _create_book_path
# _process_book
# _process_duplicate_book
# _move_book
# _save_fileless_image
# _book_should_be_moved_with_rules
# _ check_bookpath_same_as_newpath
# _get_samller_path


class TestBookmoverBase(unittest.TestCase):
    def setUp(self):
        """Sets up a bookmover object and profile the subclasses can use"""
        i18n.setup(ComicRack())
        bookmover.ComicRack = ComicRack()
        self.profile = Profile()
        self.profile.Name = "Test"
        self.profile.Mode = Mode.Move
        self.book = ComicBook()
        self.mover = BookMover(None, None, MoveReporter())
        self.mover.profile = self.profile
        self.mover._set_book_and_profile(self.book, self.profile)
        self.mover._report.create_profile_reports([self.profile], 1)

    def tearDown(self):
        print self.mover._report._log


class TestBookMoverCreateDeleteFolders(TestBookmoverBase):

    def test_create_folder_simulate(self):
        """Tests that the folder creation in simulate mode doesn't create a
        folder"""
        d = DirectoryInfo(create_path("LOTEST"))
        self.profile.Mode = Mode.Simulate
        r = self.mover._create_folder_simulated(d)
        self.assertEqual(r, MoveResult.Success)
        d.Refresh()
        self.assertFalse(d.Exists)
        print self.mover._report._log
        if d.Exists:
            d.Delete()


class TestProcessDuplicates(TestBookmoverBase):

    def test_duplicate_move_overwrite(self):
        """ Mocks passing a duplicate that needs to be overwritten to the
        main duplicate handling method.
        """
        def return_overwrite(*args, **kwargs):
            return self.DuplicateResult(1, False)
        self.duplicatehandler._duplicate_window.ShowDialog = return_overwrite
        self.mover._duplicate_handler = self.duplicatehandler
        dup_path = create_path("test overwrite.txt")
        File.Create(dup_path).Close()

        to_move_path = create_path("test to move.txt")
        File.Create(to_move_path).Close()

        c = ComicBook()
        c.FilePath = to_move_path
        try:
            b = BookToMove(c, dup_path, 0, None)
            self.assertEquals(
                self.mover._process_duplicate_book(b),
                MoveResult.Success)
            assert File.Exists(dup_path)
            self.assertFalse(File.Exists(to_move_path))
        finally:
            File.Delete(dup_path)
            if File.Exists(to_move_path):
                File.Delete(to_move_path)

    def test_duplicate_move_cancel(self):
        """ Mocks the user choosing to delete a duplicate. """
        def return_overwrite(*args, **kwargs):
            return self.DuplicateResult(2, False)
        self.duplicatehandler._duplicate_window.ShowDialog = return_overwrite
        self.mover._duplicate_handler = self.duplicatehandler
        dup_path = create_path("test overwrite.txt")
        File.Create(dup_path).Close()

        to_move_path = create_path("test to move.txt")
        File.Create(to_move_path).Close()

        c = ComicBook()
        c.FilePath = to_move_path
        try:
            b = BookToMove(c, dup_path, 0, None)
            self.assertEquals(
                self.mover._process_duplicate_book(b),
                MoveResult.Skipped)
            self.asserFalse(File.Exists(dup_path))
            self.assertTrue(File.Exists(to_move_path))
        finally:
            File.Delete(dup_path)
            if File.Exists(to_move_path):
                File.Delete(to_move_path)

    def test_duplicate_move_overwrite_simulate(self):
        """ Tests that the duplicate handling works correctly when overwrite is
        chosen with simulate mode.
        """
        def returnoverwrite(*args, **kwargs):
            return self.DuplicateResult(1, False)
        self.mover._duplicate_window.ShowDialog = returnoverwrite
        self.profile.Mode = Mode.Simulate
        dup_path = create_path("test overwrite.txt")
        File.Create(dup_path).Close()

        to_move_path = create_path("test to move.txt")
        File.Create(to_move_path).Close()

        c = ComicBook()
        c.FilePath = to_move_path
        c.FileDirectory = DirectoryInfo(to_move_path).FullName

        try:
            b = BookToMove(c, dup_path, 0, None)
            assert self.mover._process_duplicate_book(b) == MoveResult.Success
            assert File.Exists(dup_path) == True
            assert File.Exists(to_move_path) == True
        finally:
            File.Delete(dup_path)
            if File.Exists(to_move_path):
                File.Delete(to_move_path)

    def test_duplicate_overwrite_with_different_extension(self):
        """ Tests that the duplicate handling works correctly when overwrite is
        chosen with simulate mode.
        """
        def returnoverwrite(*args, **kwargs):
            return self.DuplicateResult(1, False)
        self.mover._duplicate_window.ShowDialog = returnoverwrite
        dup_path = create_path("test overwrite.tmp")
        File.Create(dup_path).Close()
        dup_file = FileInfo(dup_path)
        to_move_path = create_path("test to move.txt")
        File.Create(to_move_path).Close()
        dest_path = create_path("test.txt")
        self.book.FilePath = to_move_path
        self.book.FileDirectory = DirectoryInfo(to_move_path).FullName
        try:
            b = BookToMove(self.book, dest_path, 0, None)
            b.duplicate_different_extension = True
            b.duplicate_ext_files.append(dup_file)
            assert self.mover._process_duplicate_book(b) == MoveResult.Success
            assert File.Exists(dup_path) == False
            assert File.Exists(to_move_path) == False
            assert File.Exists(dest_path) == True
        finally:
            File.Delete(dup_path)
            if File.Exists(to_move_path):
                File.Delete(to_move_path)
            if File.Exists(dest_path):
                File.Delete(dest_path)

    def test_duplicate_overwrite_with_multiple_different_extension(self):
        """ Tests that the duplicate handling works correctly when overwrite is
        chosen with simulate mode.
        """
        def returnoverwrite(*args, **kwargs):
            return self.DuplicateResult(1, False)
        self.mover._duplicate_window.ShowDialog = returnoverwrite
        dup_path = create_path("testbook.cbt")
        File.Create(dup_path).Close()
        dup_path2 = create_path("testbook.cbr")
        File.Create(dup_path2).Close()
        self.mover.profile.DifferentExtensionsAreDuplicates = True
        to_move_path = create_path("test to move.txt")
        File.Create(to_move_path).Close()
        dest_path = create_path("testbook.cbz")
        self.book.FilePath = to_move_path
        self.book.FileDirectory = DirectoryInfo(to_move_path).FullName
        try:
            b = BookToMove(self.book, dest_path, 0, None)
            b.duplicate_different_extension = True
            b.duplicate_ext_files.append(FileInfo(dup_path))
            b.duplicate_ext_files.append(FileInfo(dup_path2))
            assert self.mover._process_duplicate_book(b) == MoveResult.Success
            self.assertFalse(File.Exists(dup_path))
            self.assertFalse(File.Exists(dup_path2))
            self.assertFalse(File.Exists(to_move_path))
            self.assertTrue(File.Exists(dest_path))
        finally:
            if File.Exists(dup_path): File.Delete(dup_path)
            if File.Exists(dup_path2): File.Delete(dup_path)
            if File.Exists(to_move_path): File.Delete(to_move_path)
            if File.Exists(dest_path): File.Delete(dest_path)


class TestDuplicateHandler(TestBookmoverBase):

    class MockDuplicateWindow(object):
        def ShowDialog(self, *args, **kwargs):
            pass

    def setUp(self):
        TestBookmoverBase.setUp(self)
        self.duplicatehandler = DuplicateHandler(MoveReporter(), [])
        self.duplicatehandler._duplicate_window = self.MockDuplicateWindow()
        self.profile = Profile()
        self.profile.Mode = Mode.Move

    def test_delete_duplicate(self):
        """ This tests that the duplicate delete code works as expected in a
        normal usage."""
        try:
            dup_path = Path.Combine(Path.GetTempPath(), "test duplicate.txt")
            f1 = File.Create(dup_path)
            f1.Close()
            self.mover._duplicate_handler._delete_duplicate(dup_path)
            assert not File.Exists(dup_path)
        finally:
            File.Delete(dup_path)

    def test_delete_duplicate_in_use(self):
        """ This tests that the duplicate delete code fails gracefully when
        the duplicate file is in use."""
        try:
            dup_path = Path.Combine(Path.GetTempPath(), "test duplicate.txt")
            f1 = File.Create(dup_path)
            self.assertEqual(
                self.mover._duplicate_handler._delete_duplicate(dup_path),
                MoveResult.Failed)
            assert File.Exists(dup_path)
        finally:
            f1.Close()
            File.Delete(dup_path)

    def test_create_rename_path(self):
        """ This tests the create rename path function that rename paths are
        created correctly when several exist."""
        try:
            f1 = create_path("test (1).txt")
            f2 = create_path("test (2).txt")
            File.Create(f1).Close()
            File.Create(f2).Close()
            path = create_path("test.txt")
            self.assertEqual(
                self.mover._duplicate_handler._create_rename_path(path),
                create_path("test (3).txt")
            )
        finally:
            File.Delete(f1)
            File.Delete(f2)

    class DuplicateResult(object):
        def __init__(self, action, always_do_action):
            self.action = action
            self.always_do_action = always_do_action


class TestCreateFilelessImage(TestBookmoverBase):

    def create_fileless(self, format):
        path = create_path("lotestimg." + format)
        r = None
        try:
            r = self.mover._save_fileless_image(self.book, path, Mode.Move)
        finally:
            File.Delete(path)
        return r

    def test_create_fileless_jpg(self):
        self.assertEquals(self.create_fileless("jpg"), MoveResult.Success)

    def test_create_fileless_png(self):
        self.assertEquals(self.create_fileless("png"), MoveResult.Success)

    def test_create_fileless_bmp(self):
        self.assertEquals(self.create_fileless("bmp"), MoveResult.Success)

    def test_create_fileless_simulate(self):
        path = create_path("lotestimg.jpg")
        self.mover._save_fileless_image(self.book, path, Mode.Simulate)
        self.assertFalse(File.Exists(path))

def create_path(f):
    return Path.Combine(Path.GetTempPath(), f)

if __name__ == '__main__':
    try:
        unittest.main()
    except Exception as ex:
        print ex
