import $file.^.^.property.AtlasProperty
import AtlasProperty._
import $file.^.^.property.AnnotationSource
import AnnotationSource.AnnotationSource
import $file.^.Paths

type BioMartQuerySpecification = (Map[String, String],List[String]) //filters and attributes
case class BioMartTask(atlasProperty: AtlasProperty, queries: List[BioMartQuerySpecification], destination: ammonite.ops.Path){
  def annotationSource: AnnotationSource = atlasProperty.annotationSource
  def seemsDone = destination.toNIO.toFile.exists
  def ensemblAttributesInvolved = queries.map(_._2).flatten.toSet
  override def toString = s"BioMart task for ${annotationSource} : ${queries.size} queries, destination: ${destination}"
}

/*
Still not sure we can use the same reference columns for both Ensembl and wbps - Maria's code has them in, but they don't validate right
*/
def ensemblNameOfReferenceColumn(atlasProperty: AtlasProperty) = {
  atlasProperty match {
    case AtlasBioentityProperty(species, bioentityType, atlasName)
      => bioentityType.value
    case AtlasArrayDesign(species, atlasName)
      => "ensembl_gene_id"
  }
}

def queriesForAtlasProperty(atlasProperty: AtlasProperty, desiredCorrespondingProperties : List[String]) = {
  val shards =
      AnnotationSource.getValue(atlasProperty.annotationSource,"chromosomeName")
      .right.map(_.split(",").toList.map{case chromosome => Map("chromosome_name"->chromosome)})
      .left.map{missingChromosome => List(Map[String,String]())}
      .merge

  desiredCorrespondingProperties
  .flatMap{case ensemblName =>
    val attributes =
      List(
        ensemblNameOfReferenceColumn(atlasProperty)
        ,ensemblName
      )

    shards.map((_,attributes))
  }
}

def retrievalPlanForAtlasProperty(atlasProperty: AtlasProperty, desiredCorrespondingProperties : List[String]) = {
  BioMartTask(
    atlasProperty,
    queriesForAtlasProperty(atlasProperty, desiredCorrespondingProperties),
    Paths.destinationFor(atlasProperty)
  )
}


def allTasks = {
  AtlasProperty.getMappingWithDesiredCorrespondingProperties
  .map{ case (atlasProperty, desiredCorrespondingProperties) =>
    retrievalPlanForAtlasProperty(atlasProperty, desiredCorrespondingProperties)
  }
  .toSeq
}
