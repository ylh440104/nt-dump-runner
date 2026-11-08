import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataTypeComponent;
import ghidra.program.model.data.DataTypeManager;
import ghidra.program.model.data.Structure;
import ghidra.program.model.data.Union;
import java.io.PrintWriter;
import java.util.Iterator;

public class DumpTypes extends GhidraScript {
    @Override
    public void run() throws Exception {
        String out = getScriptArgs()[0];
        DataTypeManager dtm = currentProgram.getDataTypeManager();
        try (PrintWriter pw = new PrintWriter(out, "UTF-8")) {
            pw.println("kind\towner\tname\tfield\toffset\tlength\ttype");
            Iterator<DataType> it = dtm.getAllDataTypes();
            while (it.hasNext()) {
                DataType dt = it.next();
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
                } else if (dt instanceof ghidra.program.model.data.Enum e) {
                    for (String n : e.getNames()) {
                        pw.printf("ENUM\t%s\t%s\t%s\t%d\t%d\t%n",
                            e.getPathName(), e.getName(), n, e.getValue(n), e.getLength());
                    }
                }
            }
        }
        println("types written to " + out);
    }
}
