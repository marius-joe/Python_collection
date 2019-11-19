#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Utilities for file backups
#  v0.3.2
# ******************************************

# under Construction

"""Utilities for file backups"""

import sys, os, glob
import string
import pickle

class output_versioned:
    """
    Like a file object opened for output, but with versioned backups
    of anything it would overwrite in other cases
    """

    def __init__(self, pathname, num_savedVersions=3):
        """
        Create a new output file. pathname is the name of the file to
        (over)write. num_savedVersions lists how many of the most recent
        versions of pathname to save.
        """
        self._pathName = pathname
        self._pathName_tmp = f"{self._pathName}.~new~"
        self._num_savedVersions = num_savedVersions
        self._fo = open(self._pathName_tmp, "wb")

    def __del__(self):
        self.close()

    def close(self):
        if self._fo:
            self._fo.close()
            self._replaceCurrentFile()
            self._fo = None

    def asFile(self):
        """
        Return self's shadowed file object, since pickle is
        quite insistent on working with a real file object.
        """
        return self._fo

    def __getattr__(self, attr):
        """ Delegate operations to self's open file object. """
        return getattr(self._fo, attr)

    def _replaceCurrentFile(self):
        """ Replace the current contents of the named file. """
        self._backupCurrentFile()
        os.rename(self._pathName_tmp, self._pathName)

    def _backupCurrentFile(self):
        """ Save a numbered backup of the named file. """
        # If the file does not exist already, there is nothing to do here
        if os.path.isfile(self._pathName):
            newName = self._versionedName(self._currentRevision() + 1)
            os.rename(self._pathName, newName)

            # get rid of old versions if there are any
            if ((self._num_savedVersions is not None) and
                (self._num_savedVersions > 0)):
                self._deleteOldRevisions()

    def _versionedName(self, revision):
        """ Get pathname with a revision number appended. """
        return f"{self._pathName}.~{revision}~"

    def _currentRevision(self):
        """ Get the revision number of the largest existing backup. """
        revisions = [0] + self._revisions()
        return max(revisions)

    def _revisions(self):
        """ Get the revision numbers of all backup files. """
        revisions = []
        names_backup = glob.glob(f"{self._pathName}.~[0-9]*~")
        for name in names_backup:
            try:
                revision = int(string.split(name, "~")[-2])
                revisions.append(revision)
            except ValueError:
                # Some ~[0-9]*~ extensions may not be completely numeric
                pass
        revisions.sort()
        return revisions

    def _deleteOldRevisions(self):
        """
        Delete old versions of the file, so that at maximum
        self._num_savedVersions versions are retained.
        """
        revisions = self._revisions()
        revisions_toDelete = revisions[:-self._num_savedVersions]
        for revision in revisions_toDelete:
            pathname = self._versionedName(revision)
            if os.path.isfile(pathname):
                os.remove(pathname)

def main():
    """ main module (for isolated testing) """

    basename = "TestFile.txt"
    if os.path.exists(basename):
        os.remove(basename)
    for i in range(10):
        fo = output_versioned(basename)
        fo.write(f"This is version {i}" + "\n")
        fo.close()

    # Now there should be just 4 versions of TestFile.txt:
    suffixes_expected = ["", ".~7~", ".~8~", ".~9~"]
    versions_expected = []
    for suffix in suffixes_expected:
        versions_expected.append(f"{basename}{suffix}")
    versions_expected.sort()
    files_matching = glob.glob(f"{basename}*")
    files_matching.sort()
    for filename in files_matching:
        if filename not in versions_expected:
            sys.stderr.write(f"Found unexpected file {filename}" + "\n")
        else:
            # Unit tests should clean up after themselves:
            os.remove(filename)
            versions_expected.remove(filename)
    if versions_expected:
        sys.stderr.write("Not found expected file")
        for ev in versions_expected:
            sys.sdterr.write(" " + ev)
        sys.stderr.write("\n")

    # Finally, here's an example of how to use versioned
    # output files in concert with pickle:
    import pickle

    fo = output_versioned("pickle.dat")
    pickle.dump([1, 2, 3], fo.asFile())
    fo.close()
    os.remove("pickle.dat")



if __name__ == "__main__":
    main()