
/**
 * Hullo! This build script is responsible for creating the final RWP_Modpack.zip distributable. It
 * works by selectively copying files from `mods/` into `dist/`, preserving their file hierarchy,
 * with configuration to include or exclude specific paths/types of content.
 * 
 * Additionally, custom files can be provided, which will be copied over any files in the output
 * directory with a matching name. This is useful for adding in custom .cfg files, for instance.
 * 
 * If you're having trouble running this script, make sure that:
 * 
 *   1. You have a reasonably up-to-date Node.js installation (should be at least 16.x, you can check this with `node -v`)
 *   2. You've installed all the dependencies (with `npm install`, from the root of the repo)
 * 
 * If problems persist, message Ecliptic Industries on Scott's Discord, or raise an issue on GitHub.
 */

import {createWriteStream} from 'fs'
import {readFile, readdir} from 'fs/promises'
import {copy, rm, exists, readJSON} from 'fs-extra'
import {glob} from 'glob'
import {normalize, join} from 'path/posix'
import archiver from 'archiver'

/** Modpack version. Update this when content changes. */
const VERSION = '0.0.1'

const include_file_extensions = ['png', 'dds', 'cfg', 'mu', 'dll', 'version', 'txt', 'md']

type FileList = string[] | null


/** Metadata describing a mod, and giving context on which files from it we want to include/exclude */
interface ModDescriptor {
	name: string,
	settings: {
		src_path?: string,
		dest_path?: string
	}
	include_list: FileList,
	exclude_list: FileList,
	custom_files: FileList,
}


/**
 * Gets the path of the relevant files for a mod
 * 
 * @param mod 
 * @returns 
 */
function getSrcPath( mod: ModDescriptor ) {
	return join('mods', mod.name, mod.settings.src_path ?? '')
}


/**
 * Determine the directory which mod files should be output to
 * 
 * @param mod 
 * @param path 
 * @returns 
 */
function getDestPath( mod: ModDescriptor, path: string ) {
	// Losing my mind because the POSIX version of normalize() doesn't replace windows
	// path separators with POSIX ones.
	const stripped_path = normalize(path)
		.replace(/\\/g, '/')
		.replace(getSrcPath(mod), '')
		.replace(`overrides/${mod.name}/custom_files`, '')

	return join('dist/RWP_Modpack/GameData', mod.settings.dest_path ?? mod.name, stripped_path)
}


/**
 * Fetch all the supporting files for a particular mod (include and exclude lists, custom files, etc)
 * 
 * @param name The name of the mod to load
 */
async function getModMetadata( name: string ): Promise<ModDescriptor> {
	const meta_path = `overrides/${name}`
	
	let settings: ModDescriptor['settings'] = {}

	let include_list: FileList = null
	let exclude_list: FileList = null
	let custom_files: FileList = null
	
	if( await exists(`${meta_path}/settings.json`) )
		settings = await readJSON(`${meta_path}/settings.json`)

	// Grab the include and exclude lists
	if( await exists( `${meta_path}/include_list.txt` ) )
		include_list = (await readFile( `${meta_path}/include_list.txt`, { encoding: 'utf-8' } )).split(/\r?\n/).filter(f => f)

	if( await exists( `${meta_path}/exclude_list.txt` ) )
		exclude_list = (await readFile( `${meta_path}/exclude_list.txt`, { encoding: 'utf-8' } )).split(/\r?\n/).filter(f => f)

	// Grab a list of custom assets to copy over
	custom_files = await glob( `${meta_path}/custom_files/**/*.{${include_file_extensions.join(',')}}`)

	// Normalize settings
	settings = {
		src_path: settings.src_path ?? '',
		dest_path: settings.dest_path ?? name
	}

	return { name, settings, include_list, exclude_list, custom_files }
}


/**
 * Copies the relevant files from a mod's directory to the 'dist' folder
 * 
 * @param mod 
 */
async function copyModFiles( mod: ModDescriptor ) {
	// Build a list of specific files to include
	const to_copy = new Set<string>()

	// If there's an explicit include list, evaluate it
	if( mod.include_list ) {
		for( const line of mod.include_list ) {
			const paths = await glob(normalize(`${getSrcPath(mod)}/${line}`))

			paths.forEach( path => to_copy.add(path) )
		}
	}
	// If not, just include everything with a matching file type
	else {
		const paths = await glob(`${normalize(getSrcPath(mod))}/**/*.{${include_file_extensions.join(',')}}`)
		
		paths.forEach( path => to_copy.add(path) )
	}

	// Filter out items from the exclude list
	if( mod.exclude_list ) {
		for( const line of mod.exclude_list ) {
			(await glob(`${normalize(getSrcPath(mod))}/${line}`)).forEach( path => to_copy.delete(path) )
		}
	}

	// Add in any custom files from outside the mod's directory
	//

	// Start copying things
	for( const path of to_copy ) {
		const dest = normalize(getDestPath(mod, path))

		await copy(path, dest, {overwrite: true})
	}

	// Add in custom files
	for( const path of mod.custom_files ?? [] ) {
		const dest = normalize(getDestPath(mod, path))

		await copy(path, dest, {overwrite: true})
	}
}


/**
 * Zips up a folder
 * 
 * @param path 
 */
async function zipFolder( src: string, dest: string ) {
	const archive = archiver('zip', { zlib: { level: 9 }});
	const stream = createWriteStream(dest);

	 await new Promise<void>((resolve, reject) => {
		archive
			.directory(src, false)
			.on('error', err => reject(err))
			.pipe(stream)

		stream.on('close', () => resolve())
		archive.finalize()
	})
}


async function main() {
	console.log(`Building RWP Modpack...`)
	console.time('build')

	// Clear out the existing dist folder
	if( await exists('dist/') )
		await rm('dist/', {recursive: true})

	// Get all the mods themselves
	const mods = await readdir('mods')

	// Copy over mod files
	for( const mod_name of mods ) {
		console.log(`  Copying ${mod_name}`)

		await copyModFiles( await getModMetadata(mod_name) )
	}

	// Copy the readme
	await copy('README.md', 'dist/RWP_Modpack/README.md', {overwrite: true})

	console.log(`Creating zip folder...`)
	console.time('zip')

	// Zip up the RWP folder
	await zipFolder( 'dist/RWP_Modpack', `dist/RWP_Modpack-v${VERSION}.zip` )
	
	console.timeEnd('zip')
	console.timeEnd('build')

	console.log(`\nAll done! Fly dangerously!`)
}

main()
