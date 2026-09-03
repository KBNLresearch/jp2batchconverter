# KB Image Workflow Tool

## About this software

Kbiw converts image files in digitisation batches to JP2 (JPEG 2000 Part 1) format using the [Grok](https://github.com/GrokImageCompression/grok) codec. It clones the structure of the input directory, and then replicates it in the output directory. The JP2 images are then subjected to the following quality checks:

1. Pixel comparison between each pair of source and destination images (using [libvips](https://www.libvips.org/) and [pyvips](https://libvips.github.io/pyvips/)).
2. Check of extracted technical properties (using [jpylyzer](https://jpylyzer.openpreservation.org/)) against a user-defined [Schematron](http://en.wikipedia.org/wiki/Schematron) profile.

The software also generates checksums of all converted images.

## Dependencies

- Python (tested with versions 3.12.3 and 3.14.5)
- [Grok JPEG 2000 codec](https://github.com/GrokImageCompression/grok) (tested with version ??)
- [Libvips](https://www.libvips.org/)
- [ExifTool](https://exiftool.org/)

## Installation of dependencies

### Grok (all platforms)

1. Download the latest binaries of the Grok image compression software for your platform from:

   <https://github.com/GrokImageCompression/grok/releases>

2. Extract the ZIP file to your local file system, and make a note of the installation location. You'll need to enter this later in the kbiw configuration file.

### Libvips

#### Linux (Ubuntu, Linux Mint)

Install libvips using:

```
sudo apt install libvips-dev --no-install-recommends
```

#### macOS

Install libvips using:

```
brew install vips
```

#### Windows

1. Download the latest release from the [build-win64-mxe repository](https://github.com/libvips/build-win64-mxe/releases). For a 64 bit Windows system you need the ZIP file that follows the "vips-dev-x64-all-x.y.z.zip" naming pattern (e.g. vips-dev-x64-all-8.18.2.zip).

2. Extract the ZIP file to your local file system, and make a note of the installation location (e.g. "C:\vips-dev"). You'll need to enter this later in the kbiw configuration file.

### ExifTool

#### Linux (Ubuntu, Linux Mint)

Install ExifTool using:

```
sudo apt install libimage-exiftool-perl
```

#### macOS

Install ExifTool using:

```
brew install exiftool
```

#### Windows

1. Download the 64-bit Windows executable from the [ExifTool website](https://exiftool.org/index.html).

2. Extract the ZIP file to your local file system.

3. In the extracted folder, rename the ExifTool executable ("exiftool(-k).exe") to "exiftool.exe.

4. Make a note of the full path to the executable (e.g. "C:\exiftool\exiftool.exe"). You'll need to enter this later in the kbiw configuration file.

## Installation of kbiw

As of 2026, [uv](https://docs.astral.sh/uv/) appears to be the most straightforward tool for installing Python applications on a variety of platforms (Linux, MacOS, Windows). However, the default KB Windows security policy blocks any applications that are installed in this way. For these machines, we have to install kbiw with pip, after which kbiw can be run as a Python module. For completeness, both installation methods (uv installation and pip installation) are decribed below.

### uv installation (all platforms)

First, check if uv is installed on your system by typing the uv command in a terminal:

```
uv
```

If this results in a help message, uv is installed, and you can skip directly to the "imgquad installation" section below. If not, you first need to install uv.

On Linux and MacOS you can install uv with the following command:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Alternatively, you can use wget if your system doesn't have curl installed:

```
wget -qO- https://astral.sh/uv/install.sh | sh
```

To install uv on Windows, open a Powershell terminal, and run the following command:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Regardless of the operating system, in some cases the installation script will update your system's configuration to make the location of the uv executable globally accessible. If this happens, just close your current terminal, and open a new one for these changes to take effect. Pay attention to the screen output of the installation script for any details on this.

### kbiw installation

Use the following command to install kbiw (all platforms):

```
uv tool install kbiw
```

## pip installation (Windows with software restriction policy)

As an alternative to the uv installation, you can also install kbiw with pip. This is especially useful in case of Windows policies that block running installed Python applications.

Install kbiw with:

```
python -m pip install kbiw
```

## Initialize configuration

After the installation, run kbiw once:

```
kbiw
```

For a Windows machine with a software restriction policy that blocks running Python applications, use this command instead: 

```
python -m kbiw
```

Depending on your system, kbiw will now create a configuration folder (see next section).

## Edit configuration

Before you can use kbiw, you need to edit the configuration file, which is located in the configuration folder. The configuration folder has the name "kbiw", and its location depends on your operating system:

- For Linux and MacOS, the configuration folder is a subdirectory of the location defined by the environment variable *$XDG_CONFIG_HOME*. If this variable is not set, it will be a subdirectory of the *.config* directory in the user's home folder (e.g. `/home/johan/.config/kbiw`). Note that the *.config* directory is hidden by default.
- For Windows, the configuration folder is a subdirectory of of the *AppData\Local* folder (e.g. `C:\Users\johan\AppData\Local\kbiw`).

Open the configuration file ("config.json") in a text editor, and edit the following values:

|Variable|Meaning|Examples|
|:--|:--|:--|
|grokDir|Grok installation directory|`C:/Grok` (Windows); `~/grok` (Linux)|
|exifToolExecutable|ExifTool executable|`C:/exiftool/exiftool.exe` (Windows); `/bin/exiftool` (Linux)|
|vipsBinDir|Libvips binary dir (only needed on Windows, ignored on Linux/macOS)|`C:/vips-dev/bin` (Windows)|

**IMPORTANT**: always use **forward slashes** for these variables, even on a Windows system! This is because forward slashes are not allowed in JSON. 

Here's an example for a Windows system:


```json
{
  "grokDir": "`C:/Grok",
  "exifToolExecutable": "C:/exiftool/exiftool.exe",
  "vipsBinDir": "C:/vips-dev/bin",
  :
}
```


## Using kbiw

The general syntax of kbiw is:

```
kbiw [-h] [--version] dirIn dirOut workflow
```

The command-line arguments are:

|Argument|Description|
|:-----|:--|
|dirIn|input batch directory|
|dirOut|output batch directory|
|workflow|workflow (tifftojp2-generic, tifftojp2-mh, tifftojp2-ie)|

As an example, the following command converts input batch "batch-tiff" to "output batch "batch-jp2", using the "tifftojp2-generic" workflow:

```
kbiw ./batch-tiff ./batch-jp2 tifftojp2-generic
```

## Currently implemented workflows

### tifftojp2-generic

This converts all TIFF images (identified by a ".tif" or ".tiff" file extension) in the input batch directory to corresponding JP2 images in the output batch directory. The directory structure of the input batch is replicated in the output batch. Any files in the input batch that are not TIFF images are ignored. The same is true for directories that do not contain any TIFF images. As a result, these files and directories are not included in the output batch. For each input TIFF, the workflow involves the following steps:

1. Convert the TIFF to JP2 with the [Grok](https://github.com/GrokImageCompression/grok) JPEG 2000 encoder, using the compression profile "KB_MASTER_LOSSLESS_10/06/2026".
1. Read the metadata from the input TIFF, and write these as an XMP block to the JP2 with [ExifTool](https://exiftool.org/).
1. Analyze the JP2 with [Jpylyzer](https://jpylyzer.openpreservation.org/), and evaluate its output against the [Schematron schema](./kbiw/conf/schemas/kbMaster_2026.sch) that defines the required technical properties and metadata.
1. Check if the pixel values of the JP2 are identical to those of the input TIFF, using the [libvips](https://www.libvips.org/) image processing library.
1. Calculate the JP2's SHA-512 checksum, and add this value to the checksum file of the batch.

In addition to this, it writes the following files to the root of the output batch:

### summary.xml

This is an XML file with a brief summary of the results of the workflow. Here's an example:

``` xml
<?xml version="1.0" ?>
<kbiw xmlns="http://kb.nl/ns/kbiw/v1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <kbiwVersion>0.1.2</kbiwVersion>
    <grokVersion>20.3.5</grokVersion>
    <noErrors>1</noErrors>
    <noWarnings>0</noWarnings>
    <comment>See batch manifest and log file for details on errors and warnings</comment>
</kbiw>
```

#### manifest.csv

This is a semicolon-delimited file with information about each converted image. It has the following columns:

|Column|Meaning|
|:--|:--|
|image|relative path + name of the image|
|successGrok|True/False flag that indicates if Grok's TIFF to JP2 conversion was successful|
|successExifTool|True/False flag that indicates if ExifTool's metadata copying was successful|
|palettedImage|True/False flag that is True if the output JP2 has a color palette, and False otherwise (some JP2 decoders cannot decode paletted images, so in general you may want to avoid them)|
|successPixelCheck|True/False flag that indicates if the check on the pixel values was successful|
|successJpylyzerCheck|True/False flag that indicates if the check on the image properties (Jpylyzer + Schematron) was successful|
|failedJpylyzerChecks|List of failed Jpylyzer + Schematron checks (separated by "\|" characters)|

For the MH (Middeleeuwse Handschriften) workflow, two additional columns are reported:

|Column|Meaning|
|:--|:--|
|successFileMatch|True/False flag that indicates if a file that was copied from the source batch could be matched against an entry in the corresponding checksum file|
|successChecksumCheck|True/False flag that indicates if the checksum for a file that was copied from the source batch was successful|

These are *only* reported for (access) files that were copied from the source batch. For these files, all other fields have the value "na". Conversely, for converted images these fields always have the value "na".


#### kbiw.log

Log file. If the summary file indicates any errors or warnings, the log file provides detailed information on them (look for the ERROR and WARNING messages).

#### checksums.sha512

File with SHA-512 checksums (format is compatible with the [sha512sum](https://man7.org/linux/man-pages/man1/sha512sum.1.html) tool).

### tifftojp2-generic-convertpaletted

This workflow is identical to the *tifftojp2-generic* workflow, but with the following addition:

- Convert any palette-color TIFFs to a regular (RGB or grayscale) JP2. For this, the workflow uses ExifTool to check the value of the "PhotometricInterpretation" TIFF tag. If this is "3" ("RGB Palette"), the workflow uses libvips to convert the input TIFF to a (temporary) unpaletted TIFF file. This temporary TIFF is then converted to JP2. Converting to unpaletted JP2 can be useful, because paletted JP2s are quite uncommon, and not all decoders support them. 

### tifftojp2-mh

Workflow for batches from the "Middeleeuwse Handschriften" (Medieval Manuscripts) project. This workflow is largely identical to the *tifftojp2-generic* workflow, but with the following additions:

- Read concordance tables from the input batch, and write corresponding concordance tables to the output batch, and update all references to TIFF images to JP2. Also add file path (relative to batch root) to each entry.
- Perform a two-way check on the output concordance tables: first check that all JP2 images defined in the concordance tables exist in the output batch, and then also check that all JP2 images in the output batch are defined in the concordance tables.
- Create verbatim copies of the directories "Pakbon" and "Access_Rename". For the latter, check that all checksum values are identical to the values in the source batch.

### tifftojp2-ie

Workflow for batches from the "Indisch Erfgoed" program. This workflow is largely identical to the *tifftojp2-generic* workflow, but with the following addition: 

- Create verbatim copies of the directories "Afgeleiden", "Rapportages_meetresultaten", "Rapportages_onregelmatigheden" and "rapporten HeronQAE TC 5".

## Compression profiles

The file "cprofiles.json" in the configuration defines a set of compression profiles, which define the JPEG 20000 compression options used by Grok. Make sure to *not* change these (unless you know what you're doing), as it may result in unexpected behaviour.

## Schemas

Schemas contain the Schematron rules on which the Jpylyzer check is based. Some background information about this type of rule-based validation can be found in [this blog post](https://www.bitsgalore.org/2012/09/04/automated-assessment-jp2-against-technical-profile). Currently the following schemas are included:

### kbMaster_2026.sch

This is a schema for digitised medieval manuscripts.


<!--

It includes the following checks:

|Check|Value|
|:---|:---|
|Image format|TIFF|
|ICC profile name|eciRGB v2|
|XResolution TIFF tag|tag exists|
|YResolution TIFF tag|tag exists|
|XResolution value|600 (+/- 1) |
|YResolution value|600 (+/- 1) |
|ResolutionUnit TIFF tag|tag exists|
|ResolutionUnit value|2 (inches)|
|ImageWidth TIFF tag|tag exists|
|ImageLength TIFF tag|tag exists|
|BitsPerSample TIFF tag|tag exists|
|BitsPerSample value|'8 8 8'|
|ICCProfile TIFF tag|tag exists|
|Copyright TIFF tag|tag exists|
|NewSubfileType TIFF tag|at most 1 instance of this tag|
|SubIFDs TIFF tag|tag does not exist|
|Compression EXIF tag|tag exists|
|Compression|1 (Uncompressed)|
|Software EXIF tag|tag exists|
|Software value|not empty|
|DateTimeOriginal EXIF tag|tag exists|
|DateTimeOriginal value|not empty|
|Model EXIF tag|tag exists|
|Model value|not empty|
|Make EXIF tag|tag exists|
|Make value|not empty|
|ShutterSpeedValue EXIF tag|tag exists|
|ShutterSpeedValue value|not empty|
|ApertureValue EXIF tag|tag exists|
|ApertureValue value|not empty|
|ISOSpeedRatings EXIF tag|tag exists|
|ISOSpeedRatings value|not empty|
|photoshop:Headline|defined in XMP metadata as either element `rdf:RDF/rdf:Description/photoshop:Headline`, or attribute `rdf:RDF/rdf:Description/@photoshop:Headline`|
|photoshop:Headline value|not empty|
|photoshop:Credit|defined in XMP metadata as either element `rdf:RDF/rdf:Description/photoshop:Credit`, or attribute `rdf:RDF/rdf:Description/@photoshop:Credit`|
|photoshop:Credit value|not empty|


### mh-2025-tiff-300.sch

This schema is identical to the mh-2025-tiff-600.sch schema, except for the checks on the XResolution and YResolution values:

|Check|Value|
|:---|:---|
|XResolution value|300 (+/- 1) |
|YResolution value|300 (+/- 1) |

-->

## Licensing

KBiw is released under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). Parts of the code were inspired by the Bodleian's [Image Processing](https://github.com/bodleian/image-processing) library.



