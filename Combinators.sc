import $file.Annsrcs

/*
This is just a doodle of how to combine results.
Don't be too attached to it. :)
*/
def doAll[In](f: In => Either[String, _])(ins: Seq[In]) : Either[String, Unit] = {
  ins.flatMap{ case in =>
    f(in) match {
      case Left(err)
        => Some((in,err))
      case Right(())
        => None
    }
  }.toList match {
    case List()
      => Right(())
    case x
      => Left(s"${x.size} errors:\n ${x.mkString("\n")}")
  }
}

def speciesList() = ammonite.ops.ls(Annsrcs.annsrcsPath).map(_.segments.last)


/*
A module:

prepares itself for doing these tasks:
- figures out what auxiliary information it needs
- validates that it can do it

does them but at a pace the upstream wants:
- do requests

so, BioMart shouldn't know that we save results to a file :)

How about Future[Arg, Result]


def doAsync[In, Result](f: In => scala.concurrent.Future[Either[String, Result]])(ins: Seq[In])(implicit ec: scala.concurrent.ExecutionContext) = {
  //you can Future.sequence
}

*/
