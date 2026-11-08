import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.*;
import java.io.PrintWriter;

public class DumpTypes extends GhidraScript {
    @Override
    public void run() throws Exception {
        String out = getScriptArgs()[0];
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        try (PrintWriter pw = new PrintWriter(out, "UTF-8")) {
            pw.println("kind\towner\tname\tfield\toffset\tlength\ttype");
            for (DataType dt : dtm.getAllDataTypes()) {
                if (dt instanceof Structure s) {
                    if (s.getNumComponents() == 0) continue;
                    pw.printf("STRUCT\t%s\t%s\t\t0\t%d\t%n", s.getPathName(), s.getName(), s.getLength());
                    for (DataTypeComponent c : s.getComponents()) {
                        pw.printf("FIELD\t%s\t%s\t%s\t%d\t%d\t%s%n",
                            s.getPathName(), s.getName(),
                            c.getFieldName() == null ? "" : c.getFieldName(),
                            c.getOffset(), c.getLength(), c.getDataType().getDisplayName());
                    }
                } else if (dt instanceof Union u) {
                    pw.printf("UNION\t%s\t%s\t\t0\t%d\t%n", u.getPathName(), u.getName(), u.getLength());
                    for (DataTypeComponent c : u.getComponents()) {
                        pw.printf("UFIELD\t%s\t%s\t%s\t%d\t%d\t%s%n",
                            u.getPathName(), u.getName(),
                            c.getFieldName() == null ? "" : c.getFieldName(),
                            c.getOffset(), c.getLength(), c.getDataType().getDisplayName());
                    }
                } else if (dt instanceof Enum e) {
                    for (EnumValue v : e.getValues()) {
                        pw.printf("ENUM\t%s\t%s\t%s\t%d\t%d\t%n",
                            e.getPathName(), e.getName(), v.getName(), v.getValue(), e.getLength());
                    }
                }
            }
        }
        println("types written to " + out);
    }
}
