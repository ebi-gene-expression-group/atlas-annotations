import ammonite.ops._
val PROJECT_ROOT = pwd // because we will call Ammonite like that

if (!(PROJECT_ROOT/"annsrcs").isDir){
  throw new RuntimeException("Annotations directory not found, possibly ammonite calls this from a wrong place: "+(PROJECT_ROOT/"annsrcs"))
}


lazy val PATH_BIOENTITY_PROPERTIES = Option(System.getenv.get("PATH_BIOENTITY_PROPERTIES")).map(Path(_)).filter(_.isDir) match {
  case Some(path)
  => path
  case None
  => {
    throw new RuntimeException("export $PATH_BIOENTITY_PROPERTIES as an environment variable")
    null
  }
}

/*
 TODO within $PATH_BIOENTITY_PROPERTIES we should check that certain directories exists,
 such as go, interpro, etc.
 */

lazy val alternativeToCanonicalGoTermMapping = {
  (read.lines!(PATH_BIOENTITY_PROPERTIES /"go" / "go.alternativeID2CanonicalID.tsv"))
  .flatMap{ case line =>
      line.split("\t").toList match {
        case List(mapping, mapped)
          => Some((mapping,mapped))
        case _
          => None
      }
  }.toMap
}

/**
  * Default paths for annotation sources, within the project.
  * If you wish to override them, set the env var ANNOTATION_SOURCES
  * to a list of paths separated by colon (:). This is useful to
  * run the analysis for a single organism. For instance, if you copy
  * cp annsrcs/ensembl/homo_sapiens my_directory/ensembl/homo_sapiens
  * cp annsrcs/wpbs/c_elegans my_directory/wpbs_v2/c_elegans
  * and then setup:
  * export ANNOTATION_SOURCES=my_directory/ensembl:my_directory/wpbs_v2
  * and then run the code, it will only run for those organisms.
  * You could of course add multiple organisms to a single directory and give it without :
  * to ANNOTATION_SOURCES.
  */
val annsrcsPath = PROJECT_ROOT/"annsrcs"/"ensembl"
val wbpsAnnsrcsPath = PROJECT_ROOT/"annsrcs"/"wbps"

lazy val ANNOTATION_SOURCES: Seq[Path] = Option(System.getenv.get("ANNOTATION_SOURCES")).map(_.split(":").map(Path(_)).filter(exists).filter(_.isDir)) match {
  case Some(paths) => ((paths.map(ls! _).flatten) ++ (List())).toList
  case None => ((ls! wbpsAnnsrcsPath) ++ (ls! annsrcsPath))
}

def annotationSources: Seq[Path] = ANNOTATION_SOURCES.filter { case path =>
    path.isFile && path.segments.toList.last.matches("[a-z]+_[a-z]+")
  }

/**
 EXPERIMENT_SOURCES should be defined as an environment variable as a list of
 colon (:) delimited paths where one would expect to find experiment directories

 In particular for production, one would expect here paths to proteomics experiments,
 rna-seq experiments, microarray experiments, rna-seq experiments, etc.

 TODO add a warning when a given path is not considered valid.

 WARNING: some classes use elements in the path to make certain decisions,
 for instance array design related classes expect to find "microarray" in certain
 paths. TODO move way from such path based decisions.
 */
val EXPERIMENT_SOURCES: List[Path] = Option(System.getenv.get("EXPERIMENT_SOURCES"))
  .map(_.split(":").map(Path(_)).filter(exists).filter(_.isDir))
match {
  case Some(paths) => paths.toList
  case None => {
    throw new RuntimeException("export $EXPERIMENT_SOURCES as an environment variable, where each directory with experiments is separated by a colon :")
    null
  }
}

println("Using the following paths for sources of experiments:")
EXPERIMENT_SOURCES.map(println(_))

/*
 For each path to experiments, we list all directories that begin with 'E-'
 */
lazy val ANALYSIS_EXPERIMENTS = EXPERIMENT_SOURCES.map(ls(_)).flatten.filter(_.toString startsWith "E-")
