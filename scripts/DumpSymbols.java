import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolTable;
import java.io.PrintWriter;

public class DumpSymbols extends GhidraScript {
    @Override
    public void run() throws Exception {
        String out = getScriptArgs()[0];
        SymbolTable st = currentProgram.getSymbolTable();
        try (PrintWriter pw = new PrintWriter(out, "UTF-8")) {
            pw.println("address\ttype\tnamespace\tname");
            for (Symbol s : st.getAllSymbols(true)) {
                pw.printf("%s\t%s\t%s\t%s%n",
                    s.getAddress(), s.getSymbolType(),
                    s.getParentNamespace().getName(true), s.getName(true));
            }
        }
        println("symbols written to " + out);
    }
}
