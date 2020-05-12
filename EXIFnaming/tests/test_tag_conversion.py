import unittest

from EXIFnaming.helpers.tag_conversion import process_to_tag, FilenameAccessor


class TagConversionTest(unittest.TestCase):
    def test_process_to_tag_HDR(self):
        out = process_to_tag("HDR-E2")
        self.assertEqual(["HDR-E", "HDR"], out)

    def test_process_to_tag_HDRT(self):
        out = process_to_tag("HDR-E-Nb$123[")
        self.assertEqual(['HDR-E-Nb', 'HDR', 'Tone Mapping'], out)

    def test_process_to_tag_PANO(self):
        out = process_to_tag("PANO")
        self.assertEqual(['PANO', 'Panorama'], out)

    def test_process_to_tag_PANO2(self):
        out = process_to_tag("PANO2")
        self.assertEqual(['PANO', 'Panorama'], out)

    def test_process_to_tag_PANO_tiff(self):
        out = process_to_tag("PANO-tiff")
        self.assertEqual(['PANO-tiff', 'Panorama'], out)


class FilenameAccessorTest(unittest.TestCase):
    def test_sorting(self):
        filenameAccessor = FilenameAccessor("ISL190727_250_HDR-Ls-Nb_Dettifoss_Selfoss_RET_PANO.jpg")
        self.assertEqual("ISL190727_250_HDR-Ls-Nb_RET_PANO_Dettifoss_Selfoss.jpg", filenameAccessor.sorted_filename())

if __name__ == '__main__':
    unittest.main()
