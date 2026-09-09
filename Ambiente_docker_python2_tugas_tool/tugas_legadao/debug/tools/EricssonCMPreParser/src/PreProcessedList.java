import java.io.Serializable;
import java.util.ArrayList;

public class PreProcessedList implements Serializable
{
    ArrayList<String> ppFiles = new ArrayList<String>();

    public PreProcessedList(ArrayList<String> ppFiles)
    {
        this.ppFiles = ppFiles;
    }

    public ArrayList<String> getPpFiles()
    {
        return this.ppFiles;
    }

    public void addFileToList(String filename)
    {
        this.ppFiles.add(filename);
    }
}
