package water.api;

import java.io.IOException;
import java.io.PrintWriter;

import org.apache.hadoop.fs.Path;

import water.DKV;
import water.hdfs.PersistHdfs;
import water.util.Log;

import com.google.gson.*;
import com.google.gson.internal.Streams;

public class ImportHdfs extends Request {
  public class PathArg extends TypeaheadInputText<String> {
    public PathArg(String name) {
      super(TypeaheadHdfsPathRequest.class, name, true);
    }
    @Override protected String parse(String input) throws IllegalArgumentException {
      return input;
    }
    @Override protected String queryDescription() { return "existing HDFS path"; }
    @Override protected String defaultValue() { return null; }
  }

  protected final PathArg _path = new PathArg("path");

  public ImportHdfs() {
    _requestHelp = "Imports the given HDFS path.  All nodes in the "
        + "cloud must have permission to access the HDFS path.";
    _path._requestHelp = "HDFS path to import.";
  }

  @Override
  protected Response serve() {
    JsonArray succ = new JsonArray();
    JsonArray fail = new JsonArray();
    String pstr = _path.value();
    try {
      PersistHdfs.addFolder(new Path(pstr), succ, fail);
    } catch( IOException e ) {
      StringBuilder sb = new StringBuilder();
      PrintWriter pw = new PrintWriter(Streams.writerForAppendable(sb));
      e.printStackTrace(pw);
      pw.flush();
      Log.err(e);
      return Response.error(sb.toString());
    }
    DKV.write_barrier();
    JsonObject json = new JsonObject();
    json.add(NUM_SUCCEEDED, new JsonPrimitive(succ.size()));
    json.add(SUCCEEDED, succ);
    json.add(NUM_FAILED, new JsonPrimitive(fail.size()));
    json.add(FAILED, fail);
    Response r = Response.done(json);
    r.setBuilder(SUCCEEDED + "." + KEY, new KeyCellBuilder());
    // Add quick link
    if (succ.size() > 1)
      r.addHeader("<div class='alert'>" //
          + Parse.link("*"+pstr+"*", "Parse all into hex format") + " </div>");
    return r;
  }
}
