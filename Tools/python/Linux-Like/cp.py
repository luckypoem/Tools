from shutil import make_archive, copy2, copytree, move, rmtree, copyfile
from tempfile import mkdtemp
from logging import info, basicConfig, INFO
from os.path import join
from os import mkdir
from argparse import ArgumentParser


# Check if the wanted archive format can be used also returns it
def getFormat(path):
    # Reference for any ztar format
    reference = {'.tar.gz': 'gztar', '.tar.bz': 'bztar', '.tar.xz': '.xztar'}
    if path[-4:] in ('.zip', '.tar'):
        archive_format = path[-3:]
    else:
        if reference.setdefault(path[-7:], False):
            archive_format = reference[path[-7:]]
        else:
            archive_format = 'zip'
    # Debug
    info(f'Using: {archive_format}')
    return archive_format


# Handler for the cp command
class CPHandler:
    def __init__(self):
        # Source of data
        self.__source = None
        # Dest of data
        self.__dest = None
        # Verbose mode
        self.__verbose = None
        # Preserve metadata
        self.__preserve = copyfile
        # Copy sources to directory (target)
        self.__targetAsDirectory = None

    # Set the destination file
    def Dest(self, dest):
        dest = dest.replace('\\', '/')
        if '/' not in dest:
            dest = './' + dest
        self.__dest = dest

    # Set the source file
    def Source(self, source):
        source = source.replace('\\', '/')
        if '/' not in source:
            source = './' + source
        self.__source = source

    # Set preserve metadata
    # --preserve[=ATTR_LIST]
    #              preserve the specified attributes (default:
    #              mode,ownership,timestamps), if possible additional attributes:
    #              context, links, xattr, all
    def setPreserve(self, value):
        if value:
            self.__preserve = copy2

    # Set verbose
    # -v, --verbose
    #              explain what is being done
    def setVerbose(self, value):
        if value:
            basicConfig(level=INFO, format='%(message)s')

    # Copy all the source files to the folder destination
    # -t, --target-directory=DIRECTORY
    #          copy all SOURCE arguments into DIRECTORY
    def setTargetDirectory(self, value):
        if value:
            self.__targetAsDirectory = value

    ## Copy functions
    # Normal copy function for files
    def normal_copy(self):
        sources = self.__source.split(';')
        if self.__targetAsDirectory:
            dest = self.__dest
            try:
                mkdir(dest)
            except Exception as e:
                info(str(e))
            for file in sources:
                try:
                    print(file)
                    self.__preserve(file, join(dest, file.split('/')[-1]))
                    info(f'File {file} copied to {dest}')
                except Exception as e:
                    info(str(e))
        else:
            dest = self.__dest.split(';')
            if len(dest) != len(sources):
                info('Wrong number of destinations or sources')
                exit(-1)
            for number, file in enumerate(sources):
                try:
                    self.__preserve(file, dest[number])
                    info(f'File {file} copied to {dest}')
                except Exception as e:
                    info(str(e))

    # Create archieve of a folder
    # -a, --archive
    #              same as -dR --preserve=all
    def archive(self):
        # Create a temporal location to save only a moment the archive
        # This way we except having a archive inside another (infinite loop)
        temporal_location = mkdtemp()
        try:
            # Get the archive format
            archive_format = getFormat(self.__dest)
            # Temporary archive name
            temporary_name = str(hash(self.__dest) - hash(self.__source))[1:]
            # Temporal archive path
            archive_name = join(temporal_location, temporary_name)
            splited_source = self.__source.split('/')
            # Root directory
            root_dir = self.__source[:len(self.__source) - len(splited_source[-1])]
            # base Directory
            base_dir = splited_source[-1]
            # Check for anu error in root and base
            if not len(root_dir):
                root_dir = '.'
            if not len(base_dir):
                base_dir = '.'
            # Make a archive of the source directory
            make_archive(archive_name, archive_format, root_dir, base_dir, verbose=self.__verbose, )
            # When the format wanted is not zip or tar
            if len(archive_format) > 3:
                archive_format = f'tar.{archive_format[:2]}'
            # Move the archive created to the wanted destination
            move(f'{archive_name}.{archive_format}', self.__dest)
            info('Done, archive successfully created')
        except Exception as e:
            info(str(e))
        # Always remove the temporary file
        finally:
            # remove that tempory folder created and everything inside it
            rmtree(temporal_location)
            info('Temporary file removed')

    # Recursive copy of a folder
    # -R, -r, --recursive
    #              copy directories recursively
    def recursive(self):
        copytree(self.__source, self.__dest, copy_function=self.__preserve)


def main(args=None):
    if not args:
        parser = ArgumentParser()
        parser.add_argument('Source', help='Source1;Source2;..SourceN')
        parser.add_argument('Dest', help='Dest1;Dest2;..DestN')
        parser.add_argument('-R', '-r', '--recursive', help='Recursive copy of a folder', action='store_const',
                            const=True, default=False, dest='recursive')
        parser.add_argument('-a', '--archive',
                            help='Create archive of a folder in any of this formats (zip,tar,tar.gz,tar.xz,tar.bz)',
                            action='store_const', const=True, default=False, dest='archive')
        parser.add_argument('-t', '--target-directory', help='Use the destination as a folder for all the source files',
                            action='store_const',
                            const=True, default=False, dest='setTargetDirectory')
        parser.add_argument('-v', '--verbose', dest='setVerbose', help='Set verbose mode', action='store_const',
                            const=True, default=False)
        parser.add_argument('--preserve', dest='setPreserve', help='Preserve all metadata of source[s]',
                            action='store_const',
                            const=True, default=False)

        args = vars(parser.parse_args())
    # Handler
    cp_command = CPHandler()
    # Source[s]
    cp_command.Source(args['Source'])
    # Dest[s]
    cp_command.Dest(args['Dest'])
    # Delete non necessary keys
    del args['Source'], args['Dest']
    # Set cpy function to use
    if args['archive']:
        copy_function = getattr(cp_command, 'archive')
    elif args['recursive']:
        copy_function = getattr(cp_command, 'recursove')
    else:
        copy_function = getattr(cp_command, 'normal_copy')
    # Set variables
    for key in ('setVerbose', 'setPreserve', 'setTargetDirectory'):
        if args[key]:
            getattr(cp_command, key)(args[key])
    # Set all variables
    copy_function()


if __name__ == '__main__':
    main()
