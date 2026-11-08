import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import java.io.PrintWriter;

public class DumpDecomp extends GhidraScript {
    @Override
    public void run() throws Exception {
        String out = getScriptArgs()[0];
        int shard = Integer.parseInt(System.getenv().getOrDefault("SHARD", "0"));
        int shards = Integer.parseInt(System.getenv().getOrDefault("SHARDS", "1"));

        DecompInterface dec = new DecompInterface();
        dec.setOptions(new DecompileOptions());
        dec.openProgram(currentProgram);

        int total = 0, done = 0, fail = 0;
        try (PrintWriter pw = new PrintWriter(out, "UTF-8")) {
            FunctionManager fm = currentProgram.getFunctionManager();
            for (Function f : fm.getFunctions(true)) {
                if ((total++ % shards) != shard) continue;
                pw.println("\n===== " + f.getName() + " @ " + f.getEntryPoint() + " =====");
                try {
                    DecompileResults r = dec.decompileFunction(f, 120, monitor);
                    if (r != null && r.decompileCompleted()) {
                        pw.println(r.getDecompiledFunction().getC());
                        done++;
                    } else {
                        pw.println("/* FAILED */");
                        fail++;
                    }
                } catch (Exception e) {
                    pw.println("/* ERROR " + e.getMessage() + " */");
                    fail++;
                }
                if (monitor.isCancelled()) break;
            }
        }
        dec.dispose();
        println("total=" + total + " done=" + done + " fail=" + fail);
    }
}
