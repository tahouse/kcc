import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from zipfile import ZipFile

from PIL import Image

from kindlecomicconverter import comic2ebook
from kindlecomicconverter.comic2ebook import getEpubChapterStarts, getTomeChapter, getWorkFolder


class EpubChapterSplitTest(unittest.TestCase):
    def test_epub3_nav_maps_titles_to_spine_and_keeps_front_matter(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, 'OEBPS', 'Text'))
            opf_path = os.path.join(root, 'OEBPS', 'content.opf')
            opf = ET.ElementTree(ET.fromstring('''
                <package xmlns="http://www.idpf.org/2007/opf">
                  <manifest>
                    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                    <item id="cover" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>
                    <item id="c1" href="Text/chapter1.xhtml" media-type="application/xhtml+xml"/>
                    <item id="c2" href="Text/chapter2.xhtml" media-type="application/xhtml+xml"/>
                  </manifest>
                  <spine><itemref idref="cover"/><itemref idref="c1"/><itemref idref="c2"/></spine>
                </package>
            '''))
            with open(os.path.join(root, 'OEBPS', 'nav.xhtml'), 'w', encoding='utf-8') as nav:
                nav.write('''
                    <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
                      <body><nav epub:type="toc"><ol>
                        <li><a href="Text/chapter1.xhtml">Opening / Act</a></li>
                        <li><a href="Text/chapter2.xhtml#start">Finale</a></li>
                      </ol></nav></body>
                    </html>
                ''')

            starts = getEpubChapterStarts(
                opf_path,
                opf,
                {'cover': 'Text/cover.xhtml', 'c1': 'Text/chapter1.xhtml', 'c2': 'Text/chapter2.xhtml'},
                ['cover', 'c1', 'c2'],
            )

            self.assertEqual(starts, [(0, 'Opening _ Act'), (2, 'Finale')])

    def test_epub2_ncx_deduplicates_links_to_same_spine_document(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, 'OPS'))
            opf_path = os.path.join(root, 'OPS', 'content.opf')
            opf = ET.ElementTree(ET.fromstring('''
                <package xmlns="http://www.idpf.org/2007/opf">
                  <manifest>
                    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
                    <item id="c1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
                    <item id="c2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
                  </manifest>
                  <spine toc="ncx"><itemref idref="c1"/><itemref idref="c2"/></spine>
                </package>
            '''))
            with open(os.path.join(root, 'OPS', 'toc.ncx'), 'w', encoding='utf-8') as ncx:
                ncx.write('''
                    <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap>
                      <navPoint><navLabel><text>One</text></navLabel><content src="chapter1.xhtml"/></navPoint>
                      <navPoint><navLabel><text>One subsection</text></navLabel><content src="chapter1.xhtml#two"/></navPoint>
                      <navPoint><navLabel><text>Two</text></navLabel><content src="chapter2.xhtml"/></navPoint>
                    </navMap></ncx>
                ''')

            starts = getEpubChapterStarts(
                opf_path,
                opf,
                {'c1': 'chapter1.xhtml', 'c2': 'chapter2.xhtml'},
                ['c1', 'c2'],
            )

            self.assertEqual(starts, [(0, 'One'), (1, 'Two')])

    def test_epub2_ncx_recovers_broken_front_cover_target_from_guide(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, 'OEBPS'))
            opf_path = os.path.join(root, 'content.opf')
            opf = ET.ElementTree(ET.fromstring('''
                <package xmlns="http://www.idpf.org/2007/opf">
                  <manifest>
                    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
                    <item id="cover" href="titlepage.xhtml" media-type="application/xhtml+xml"/>
                    <item id="c1" href="OEBPS/chapter1.xhtml" media-type="application/xhtml+xml"/>
                  </manifest>
                  <spine toc="ncx"><itemref idref="cover"/><itemref idref="c1"/></spine>
                  <guide><reference type="cover" href="titlepage.xhtml" title="Cover"/></guide>
                </package>
            '''))
            with open(os.path.join(root, 'toc.ncx'), 'w', encoding='utf-8') as ncx:
                ncx.write('''
                    <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap>
                      <navPoint><navLabel><text>Front Cover</text></navLabel><content src="OEBPS/missing-cover.xhtml"/></navPoint>
                      <navPoint><navLabel><text>Chapter 1</text></navLabel><content src="OEBPS/chapter1.xhtml"/></navPoint>
                    </navMap></ncx>
                ''')

            starts = getEpubChapterStarts(
                opf_path,
                opf,
                {'cover': 'titlepage.xhtml', 'c1': 'OEBPS/chapter1.xhtml'},
                ['cover', 'c1'],
            )

            self.assertEqual(starts, [(0, 'Front Cover'), (1, 'Chapter 1')])

    def test_extraction_creates_one_directory_per_toc_chapter(self):
        with tempfile.TemporaryDirectory() as root:
            epub_path = os.path.join(root, 'volume.epub')
            image_path = os.path.join(root, 'page.png')
            Image.new('RGB', (10, 10), 'white').save(image_path)
            with ZipFile(epub_path, 'w') as epub:
                epub.writestr('META-INF/container.xml', '''
                    <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                      <rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles>
                    </container>
                ''')
                epub.writestr('OEBPS/content.opf', '''
                    <package xmlns="http://www.idpf.org/2007/opf">
                      <manifest>
                        <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                        <item id="p1" href="Text/one.xhtml" media-type="application/xhtml+xml"/>
                        <item id="p2" href="Text/two.xhtml" media-type="application/xhtml+xml"/>
                      </manifest>
                      <spine><itemref idref="p1"/><itemref idref="p2"/></spine>
                    </package>
                ''')
                epub.writestr('OEBPS/nav.xhtml', '''
                    <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
                      <body><nav epub:type="toc"><a href="Text/one.xhtml">One</a><a href="Text/two.xhtml">Two</a></nav></body>
                    </html>
                ''')
                epub.writestr('OEBPS/Text/one.xhtml', '<html xmlns="http://www.w3.org/1999/xhtml"><body><img src="../Images/one.png"/></body></html>')
                epub.writestr('OEBPS/Text/two.xhtml', '<html xmlns="http://www.w3.org/1999/xhtml"><body><img src="../Images/two.png"/></body></html>')
                epub.write(image_path, 'OEBPS/Images/one.png')
                epub.write(image_path, 'OEBPS/Images/two.png')

            workdir = getWorkFolder(epub_path, SimpleNamespace(tempdir=False, lightnovel=False,
                                                                legacyextract=False, split_epub_chapters=True))
            tomes = [workdir]
            had_options = hasattr(comic2ebook, 'options')
            previous_options = getattr(comic2ebook, 'options', None)
            try:
                images = os.path.join(workdir, 'OEBPS', 'Images')
                self.assertEqual(os.listdir(os.path.join(images, '0001 One')), ['0.png'])
                self.assertEqual(os.listdir(os.path.join(images, '0002 Two')), ['1.png'])

                output = os.path.join(root, 'export')
                comic2ebook.options = SimpleNamespace(
                    batchsplit=2,
                    folder_output=False,
                    format='CBZ',
                    output=output,
                    output_subfolder=True,
                    profile='OTHER',
                    targetsize=None,
                    webtoon=False,
                )
                chapter_names, _ = comic2ebook.sanitizeTree(images, comic2ebook.options)
                tomes = comic2ebook.chunk_directory(workdir)
                outputs = []
                for tome in tomes:
                    chapter_path, title = getTomeChapter(tome, chapter_names)
                    destination = comic2ebook.getOutputFilename(epub_path, output, '.cbz', f' - {title}')
                    outputs.append(comic2ebook.makeZIP(destination, chapter_path))

                self.assertEqual(
                    [os.path.relpath(path, output) for path in outputs],
                    [
                        os.path.join('volume', 'volume - 01 - One.cbz'),
                        os.path.join('volume', 'volume - 02 - Two.cbz'),
                    ],
                )
                for output_path in outputs:
                    with ZipFile(output_path) as chapter:
                        self.assertTrue(chapter.namelist())
                        self.assertTrue(all('/' not in name and '\\' not in name for name in chapter.namelist()))
            finally:
                import shutil
                if had_options:
                    comic2ebook.options = previous_options
                else:
                    del comic2ebook.options
                for tome in tomes:
                    shutil.rmtree(tome, True)


if __name__ == '__main__':
    unittest.main()