<h1>textedit-u1380611</h1>

<p><h2>R1</h2></p>
<p>
For this first release, I successfully implemented all the basics such as text editing, selection, keyboard shortcuts, and a menu bar. My approach was to ask ChatGPT to break down the entire control flow of Microsoft Notepad into simple actions such as File > Save as > File explorer popup. This worked incredibly well and I had all of these basics implemented in less than 3 prompts. I also have implemented an unsaved changes popup when closing a file you have modified and I have started on tabs/split view, although that feature won't be ready till next release.
</p>
<p>
For testing I have an AMP-generated testing suite that currently includes 90 tests. These test various functions such as file read/write, UTF-8 encoding, errors, document modeling, word wrap, etc. I plan on implementing more tests as I continue with the project, so far the tests AMP has made look correct and I haven't felt the need to edit them. AMP also does surprisingly well with modularity on it's own, and many components such as document handling, the editing pane, the file handler, and more, have all been split into their own files without the need of my instruction. Moving forward, as mentioned above, I have started on a tab and split view system that I will refine in the next release along with adding new features. 
</p>
