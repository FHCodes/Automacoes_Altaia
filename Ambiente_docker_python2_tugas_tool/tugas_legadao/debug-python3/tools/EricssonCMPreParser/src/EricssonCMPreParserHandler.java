import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;

import org.apache.commons.text.StringEscapeUtils;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

public class EricssonCMPreParserHandler extends DefaultHandler {
    private DateTimeFormatter dtf = DateTimeFormatter.ofPattern("dd-MM-yyyy HH:mm:ss");
    private String datetime;
    private LocalDateTime parseStartTime;
    private String fileName;

    private String parent;
    private String child;
    private boolean isHeader = false;
    private boolean isSubNetwork = false;
    private boolean isMeContext = false;
    private boolean outSN = false;
    private boolean outMC = true;
    private boolean verbose = true;
    private boolean deleteZone = false;
    private boolean selfTerminatedNode = false;
    private boolean escape = true;

    private String outDir;

    private ArrayList<JSONArray> globalHeader = new ArrayList<JSONArray>();
    private ArrayList<JSONArray> globalFooter = new ArrayList<JSONArray>();
    private ArrayList<File> subNetworkFilesQueue = new ArrayList<File>();
    private ArrayList<File> meContextFilesQueue = new ArrayList<File>();
    private HashMap<String,HashMap<String,Integer>> parseStats = new HashMap<String,HashMap<String,Integer>>();

    public EricssonCMPreParserHandler(String datetime, String outdir, boolean verbose, boolean outSN, boolean outMC, boolean escape)
    {
        this.datetime = datetime;
        this.outDir = outdir;
        this.verbose = verbose;
        this.outSN = outSN;
        this.outMC = outMC;
        this.escape = escape;
    }

    @Override
    public void startDocument() throws SAXException
    {
        if(this.parseStartTime == null)
        {
            this.parseStartTime = LocalDateTime.now();
        }
        System.out.println(String.format("[%s] Starting to process file %s", dtf.format(LocalDateTime.now()), this.fileName));
    }

    @Override
    public void endDocument() throws SAXException
    {
        System.out.println(String.format("[%s] Finished processing file", dtf.format(LocalDateTime.now())));
        printStats();
    }

    @Override
    @SuppressWarnings("unchecked")
    public void startElement(String uri, String localName, String qname, Attributes attrs) throws SAXException
    {
        // Remove namespace from qname
        String[] qnameList = qname.split(":");
        qname = qnameList.length > 1 ? qnameList[1] : qnameList[0];

        // Array list of attributes without namespace
        ArrayList<JSONObject> attributes = new ArrayList<JSONObject>();

        // Remove namespace from attrs
        for(int i = 0; i < attrs.getLength(); i++)
        {
            String[] attrList = attrs.getLocalName(i).split(":");
            String localNameValue = attrList.length > 1 ? attrList[1] : attrList[0];
            String[] valueList = attrs.getValue(i).split(":");
            String value = valueList.length > 1 ? valueList[1] : valueList[0];
            JSONObject obj = new JSONObject();
            obj.put(localNameValue, value);
            attributes.add(obj);
        }
        
        // Define parent and child
        this.parent = this.child;
        this.child = qname;

        if(Arrays.asList("bulkCmConfigDataFile","configData", "SubNetwork").contains(qname))
        {
            this.isHeader = true;
            
            JSONObject obj = new JSONObject();
            obj.put("name", qname);
            obj.put("selfterminated", false);
            obj.put("attrs", attributes.toString());

            JSONArray headerArray = new JSONArray();
            headerArray.add(obj);
            this.globalHeader.add(headerArray);

            JSONObject footerObj = new JSONObject();
            footerObj.put("name", qname);
            footerObj.put("selfterminated", false);
            footerObj.put("attrs", "{}");
            JSONArray footerArrayGlobal = new JSONArray();
            footerArrayGlobal.add(footerObj);
            this.globalFooter.add(footerArrayGlobal);

            if(qname.equals("bulkCmConfigDataFile"))
            {
                JSONObject footer = new JSONObject();
                footer.put("name", "fileFooter");
                footer.put("selfterminated", true);
                JSONObject dt = new JSONObject();
                dt.put("dateTime", this.datetime);
                footer.put("attrs", dt.toJSONString());
                JSONArray footerArray = new JSONArray();
                footerArray.add(footer);
                this.globalFooter.add(footerArray);
            }

            if(qname.equals("SubNetwork"))
            {
                this.isHeader = false;
                this.isSubNetwork = true;

                // Validates that SubNetwork files are a desired output
                if(this.outSN)
                {
                    // Subnetwork nodes signal the start of a file of external families
                    String fname = getFilename(this.outDir);

                    if(this.verbose)
                    {
                        System.out.println(String.format("SN: Opening file %s", fname));
                    }

                    // Open the file
                    try
                    {
                        File file = new File(fname);
                        this.subNetworkFilesQueue.add(file);

                    }
                    catch(Exception e)
                    {
                        e.printStackTrace();
                    }

                    // Update stats
                    HashMap<String,Integer> subNetworkFiles = new HashMap<String,Integer>();
                    subNetworkFiles.put("SubNetworkFiles", 1);
                    this.parseStats.put("Total", subNetworkFiles);

                    writeHeader(this.subNetworkFilesQueue.get(this.subNetworkFilesQueue.size()-1));
                }
            }
        }
        else if(qname.equals("fileHeader"))
        {
            JSONObject fhObj = new JSONObject();
            fhObj.put("name", qname);
            fhObj.put("selfterminated", true);
            fhObj.put("attrs", attributes);

            JSONArray fhArray = new JSONArray();
            fhArray.add(fhObj);

            this.globalHeader.add(fhArray);
        }
        else if(qname.equals("MeContext"))
        {
            this.isHeader = true;

            JSONObject mcHeaderObj = new JSONObject();
            mcHeaderObj.put("name", qname);
            mcHeaderObj.put("selfterminated", false);
            mcHeaderObj.put("attrs", attributes);
            
            JSONArray mcHeaderArray = new JSONArray();
            mcHeaderArray.add(mcHeaderObj);

            this.globalHeader.add(mcHeaderArray);

            JSONObject mcFooterObj = new JSONObject();
            mcFooterObj.put("name", qname);
            mcFooterObj.put("selfterminated", false);
            mcFooterObj.put("attrs", "{}");

            JSONArray mcFooterArray = new JSONArray();
            mcFooterArray.add(mcFooterObj);

            this.globalFooter.add(mcFooterArray);

            this.isMeContext = true;

            if(this.outMC)
            {
                String fname = getFilename(this.outDir);

                if(this.verbose)
                {
                    System.out.println(String.format("MC: Opening file %s", fname));
                }

                // Open the file
                File mcFile = new File(fname);
                this.meContextFilesQueue.add(mcFile);

                // Update stats
                HashMap<String,Integer> meContextFiles = new HashMap<String,Integer>();
                meContextFiles.put("MeContextFiles", 1);
                this.parseStats.put("Total", meContextFiles);

                // Write the header
                int last = this.meContextFilesQueue.size() - 1;
                writeHeader(this.meContextFilesQueue.get(last));
            }
        }
        else if(qname.equals("fileFooter"))
        {
            assert true;
        }
        else if(qname.equals("attributes") && this.parent.equals("MeContext"))
        {
            this.deleteZone = true;
        }
        else
        {
            this.isHeader = false;
            this.selfTerminatedNode = true;

            // Build the nodedict
            JSONObject nodeDict = new JSONObject();
            nodeDict.put("name", qname);
            nodeDict.put("selfterminated", false);
            nodeDict.put("attrs", attributes);

            // Check if is a SubNetwork type
            if(this.isSubNetwork && !this.isMeContext && !this.deleteZone)
            {
                if(this.outSN)
                {
                    int lastIdx = this.subNetworkFilesQueue.size() - 1;
                    writeNode(nodeDict, this.subNetworkFilesQueue.get(lastIdx));
                }
            }
            else if(this.isMeContext && !this.deleteZone)
            {
                if(this.outMC)
                {
                    int lastIdx = this.meContextFilesQueue.size() - 1;
                    writeNode(nodeDict, this.meContextFilesQueue.get(lastIdx));
                }
            }
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    public void endElement(String uri, String localName, String qname) throws SAXException
    {
        // Remove namespace from qname
        String[] qnameList = qname.split(":");
        qname = qnameList.length > 1 ? qnameList[1] : qnameList[0];

        if(qname.equals("SubNetwork"))
        {
            if(this.outSN)
            {
                // Write footer
                int lastIdx = this.subNetworkFilesQueue.size() - 1;
                writeFooter(this.subNetworkFilesQueue.get(lastIdx));
                
                this.subNetworkFilesQueue.remove(lastIdx);
            }

            this.globalHeader.remove(this.globalHeader.size()-1);
            this.globalFooter.remove(this.globalFooter.size()-1);

            this.isSubNetwork = false;
        }
        else if(qname.equals("MeContext"))
        {
            if(this.outMC)
            {
                int lastIdx = this.meContextFilesQueue.size() - 1;
                writeFooter(this.meContextFilesQueue.get(lastIdx));

                this.meContextFilesQueue.remove(lastIdx);
            }

            this.globalHeader.remove(this.globalHeader.size()-1);
            this.globalFooter.remove(this.globalFooter.size()-1);

            this.isMeContext = false;
        }
        else if(Arrays.asList("bulkCmConfigDataFile", "configData", "fileHeader", "fileFooter").contains(qname))
        {
            assert true;
        }
        else
        {
            if(this.deleteZone)
            {
                if(qname.equals("attributes"))
                {
                    this.deleteZone = false;
                }

                return;
            }

            JSONObject nodeDict = new JSONObject();
            nodeDict.put("name", qname);
            nodeDict.put("selfterminated", this.selfTerminatedNode);
            nodeDict.put("attrs", "{}");

            if(this.isSubNetwork && !this.isMeContext)
            {
                if(this.outSN)
                {
                    int lastIdx = this.subNetworkFilesQueue.size() - 1;
                    writeNodeEnd(nodeDict, this.subNetworkFilesQueue.get(lastIdx));
                }
            }
            else if(this.isMeContext)
            {
                if(this.outMC)
                {
                    int lastIdx = this.meContextFilesQueue.size() - 1;
                    writeNodeEnd(nodeDict, this.meContextFilesQueue.get(lastIdx));
                }
            }
        }
    }

    @Override
    public void characters(char[] ch, int start, int length)
    {
        this.selfTerminatedNode = false;
        
        FileWriter fw = null;
        try
        {
            int lastIdx;
            File f;

            if(this.isSubNetwork && !this.isMeContext)
            {
                lastIdx = this.subNetworkFilesQueue.size() - 1;
                if(lastIdx >= 0)
                {
                    f = this.subNetworkFilesQueue.get(lastIdx);
                    fw = new FileWriter(f, true);

                    if(this.outSN)
                    {
                        if(this.escape)
                        {
                            String content = StringEscapeUtils.escapeXml11(new String(ch, start, length));
                            fw.write(content);
                        }
                        else
                        {
                            fw.write(new String(ch, start, length));
                        }
                    }

                    // Close FileWriter
                    fw.close();
                }
            }
            else if(this.isMeContext && !this.deleteZone)
            {
                lastIdx = this.meContextFilesQueue.size() - 1;
                if(lastIdx >= 0)
                {
                    f = this.meContextFilesQueue.get(lastIdx);
                    fw = new FileWriter(f, true);

                    if(this.outMC)
                    {
                        if(this.escape)
                        {
                            String content = StringEscapeUtils.escapeXml11(new String(ch, start, length));
                            fw.write(content);
                        }
                        else
                        {
                            fw.write(new String(ch, start, length));
                        }
                    }

                    // Close FileWriter
                    fw.close();
                }
            }
        }
        catch(IOException e)
        {
            e.printStackTrace();
        }
    }

    /* Helper methods */
    private void printStats()
    {
        System.out.println("------------------------------------------------------------------------------------");
        System.out.println(String.format("--------- Parsing Started: %s", this.parseStartTime));
        System.out.println(String.format("--------- Parsing Finished: %s", this.dtf.format(LocalDateTime.now())));
        int delta = (int) ChronoUnit.SECONDS.between(this.parseStartTime, LocalDateTime.now());
        System.out.println(String.format("--------- Execution time: %s", formatTimeDelta(delta)));
        System.out.println("\n--------- Statistics:");
        System.out.println(String.format("--------- SubnetWork Files -----> %s", this.parseStats.get("Total").get("SubNetworkFiles")));
        System.out.println(String.format("--------- MeContext Files -----> %s", this.parseStats.get("Total").get("MeContextFiles")));
        System.out.println("------------------------------------------------------------------------------------");
    }

    private String formatTimeDelta(int time)
    {
        int hours = time / (60 * 60);
        int rem = time - (hours * 60 * 60);
        int minutes = rem / 60;
        int seconds = rem % 60;

        return String.format("%02d:%02d:%02d", hours, minutes, seconds);
    }

    private String getFilename(String outdir)
    {
        ArrayList<String> hierarchy = new ArrayList<String>();
        
        Iterator<JSONArray> it = this.globalHeader.iterator();
        while(it.hasNext())
        {
            JSONArray array = (JSONArray) it.next();
            JSONObject obj = (JSONObject) array.get(0);
            String name = obj.get("name").toString();

            JSONParser parser = new JSONParser();
            JSONArray attrsArray = null;
            try
            {
                attrsArray = (JSONArray) parser.parse(obj.get("attrs").toString());
            }
            catch(ParseException e)
            {
                e.printStackTrace();
            }
            
            for(Object attr : attrsArray)
            {
                JSONObject attrObj = (JSONObject) attr;
                if(attrObj.containsKey("id"))
                {
                    hierarchy.add(String.format("%s=%s", name, attrObj.get("id").toString()));
                }
            }
        }
        
        return Paths.get(this.outDir, String.join(",", hierarchy)).toString() + ".xml";
    }

    private void writeHeader(File fileHandler)
    {
        String newline = "\n";

        FileWriter fw = null;
        try
        {
            fw = new FileWriter(fileHandler, true);

            int index = 0;
            Iterator<JSONArray> it = this.globalHeader.iterator();
            while(it.hasNext())
            {
                JSONObject obj = (JSONObject) it.next().get(0);
                
                // Write newline
                newline = index == 0 ? "" : "\n";
                fw.write(String.format("%s", newline));

                // Write tabs
                fw.write(new String(new char[index]).replace("\0", "\t"));
                
                // Write name
                fw.write(String.format("<%s", obj.get("name")));

                // Loop through attributes
                JSONParser parser = new JSONParser();
                JSONArray attrsArray = null;
                try
                {
                    attrsArray = (JSONArray) parser.parse(obj.get("attrs").toString());
                }
                catch(ParseException e)
                {
                    e.printStackTrace();
                }
                
                for(Object attr : attrsArray)
                {
                    JSONObject attrObj = (JSONObject) attr;
                    for(Object key : attrObj.keySet())
                    {
                        fw.write(String.format(" %s=\"%s\"", key, attrObj.get(key)));
                    }
                }

                if(Boolean.parseBoolean(obj.get("selfterminated").toString()))
                {
                    fw.write("/>");
                }
                else
                {
                    fw.write(">");
                    index++;
                }
            }

            // Write newline
            newline = index == 0 ? "" : "\n";
            fw.write(String.format("%s", newline));

            // Write tabs
            fw.write(new String(new char[index]).replace("\0", "\t"));

            // Close file writer
            fw.close();
        }
        catch(IOException e)
        {
            e.printStackTrace();
        }
    }

    public void writeNode(JSONObject nodeObject, File fileHandler)
    {
        FileWriter fw = null;
        try
        {
            fw = new FileWriter(fileHandler, true);
            fw.write(String.format("<%s", nodeObject.get("name")));

            // Loop through attributes
            JSONParser parser = new JSONParser();
            JSONArray attrsArray = null;
            try
            {
                attrsArray = (JSONArray) parser.parse(nodeObject.get("attrs").toString());
            }
            catch(ParseException e)
            {
                e.printStackTrace();
            }
            
            for(Object attr : attrsArray)
            {
                JSONObject attrObj = (JSONObject) attr;
                for(Object key : attrObj.keySet())
                {
                    fw.write(String.format(" %s=\"%s\"", key, attrObj.get(key)));
                }
            }

            if(Boolean.parseBoolean(nodeObject.get("selfterminated").toString()))
            {
                fw.write("/>");
            }
            else
            {
                fw.write(">");
            }

            // Close File Writer
            fw.close();
        }
        catch(IOException e)
        {
            e.printStackTrace();
        }
    }

    private void writeFooter(File fileHandler)
    {
        String newline = "\n";
        int footerSize = this.globalFooter.size() - 2;

        // Reverse ArrayList
        Collections.reverse(this.globalFooter);
        
        FileWriter fw = null;
        try
        {
            fw = new FileWriter(fileHandler, true);
            
            // Create an Iterator to loop through globalFooter
            Iterator<JSONArray> it = this.globalFooter.iterator();

            int index = 0;
            while(it.hasNext())
            {
                JSONObject obj = (JSONObject) it.next().get(0);

                // Write newline
                newline = index == 0 ? "" : "\n";
                fw.write(newline);

                if(index != 0)
                {
                    if(Boolean.parseBoolean(obj.get("selfterminated").toString()))
                    {
                        fw.write(new String(new char[footerSize + 1]).replace("\0", "\t"));
                    }
                    else
                    {
                        fw.write(new String(new char[footerSize]).replace("\0", "\t"));
                    }
                }
                
                if(Boolean.parseBoolean(obj.get("selfterminated").toString()))
                {
                    fw.write(String.format("<%s", obj.get("name")));
                }
                else
                {
                    fw.write(String.format("</%s", obj.get("name")));
                }

                // Loop through attributes
                JSONParser parser = new JSONParser();
                JSONArray attrsArray = null;
                try
                {
                    attrsArray = (JSONArray) parser.parse(obj.get("attrs").toString());
                }
                catch(ParseException e)
                {
                    e.printStackTrace();
                }
                catch(ClassCastException e)
                {
                    attrsArray = new JSONArray();
                }
                
                for(Object attr : attrsArray)
                {
                    JSONObject attrObj = (JSONObject) attr;
                    for(Object key : attrObj.keySet())
                    {
                        fw.write(String.format(" %s=\"%s\"", key, attrObj.get(key)));
                    }
                }

                if(Boolean.parseBoolean(obj.get("selfterminated").toString()))
                {
                    fw.write("/>");
                }
                else
                {
                    fw.write(">");
                }

                footerSize--;
            }
        }
        catch(IOException e)
        {
            e.printStackTrace();
        }
    }

    private void writeNodeEnd(JSONObject nodeObject, File fileHandler)
    {
        FileWriter fw = null;
        try
        {
            fw = new FileWriter(fileHandler, true);
            if(Boolean.parseBoolean(nodeObject.get("selfterminated").toString()))
            {
                FileChannel fc = null;
                try
                {
                    fc = new FileOutputStream(fileHandler, true).getChannel();
                    fc.truncate(fc.size() - 1);
                    fc.close();
                }
                catch (FileNotFoundException e) {
                    e.printStackTrace();
                }
                fw.write("/>");
            }
            else
            {
                fw.write(String.format("</%s", nodeObject.get("name")));
                fw.write(">");
            }
            fw.close();
        }
        catch(IOException e)
        {
            e.printStackTrace();
        }
    }
}
