import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.xml.sax.*;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

import org.json.*;

import org.apache.commons.io.*;
import org.apache.commons.text.StringEscapeUtils;

import java.io.*;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

public class NokiaCMpreParserHandler extends DefaultHandler {
    /* Final lists to help DefaultHandler overriden methods */
    private final List<String> endElements = Arrays.asList("managedObject", "p", "list", "item");
    private final List<String> startElements = Arrays.asList("header", "log", "raml", "cmData");
    private final List<String> startElementsInner = Arrays.asList("p", "list", "item");
    
    private HashMap<String, JSONObject> config = new HashMap<String, JSONObject>();
    private HashMap<String,HashMap<String,String>> techFileList = new HashMap<String, HashMap<String,String>>();
    private ArrayList<String> fileList = new ArrayList<String>();
    private Pattern techRegex = Pattern.compile("PLMN-([^\\/]*)/(?<tech>[^\\/]*)-.*$");
    private String header = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>";
    
    private LocalDateTime startTime;
    private boolean verbose;
    private boolean readHeader = false;
    private String fileName;
    private String outDir;
    private String configsDir;
    private String configFile;
    private String distName;
    private String footer = "";
    private String toWrite = "";
    private String tech;
    
    public NokiaCMpreParserHandler(String fileName, String outDir, String configsDir, boolean verbose) throws IOException
    {
        this.fileName = fileName;
        this.outDir = outDir;
        this.configsDir = configsDir;
        this.verbose = verbose;

        if(this.configsDir == "")
        {
            this.configsDir = "/opt/alticelabs/namf/tools/Configs/Nokia_preParser/";
            File dir = new File(this.configsDir);
            String[] files = dir.list();
            
            List<String> configFiles = new ArrayList<String>();
            Pattern regex = Pattern.compile("^.*.json$");
            
            try
            {
                for(String file : files)
                {
                    Matcher m = regex.matcher(file);
                    boolean match = m.matches();
                    if(match)
                    {
                        configFiles.add(this.configsDir+file);
                    }
                }
            }
            catch(NullPointerException e)
            {
                System.out.print(String.format("[CRITICAL] %s was not found or it's empty", this.configsDir));
                System.exit(0);
            }
            
            for(String jsonFile : configFiles)
            {
                try 
                {
                    String basename = new File(jsonFile).getName();
                    String keyName = basename.substring(0, basename.lastIndexOf("."));
                    
                    InputStream is = new FileInputStream(jsonFile);
                    try
                    {
                        String jsonTxt  = IOUtils.toString(is, "UTF-8");
                        JSONObject json = new JSONObject(jsonTxt);
                        this.config.put(keyName, json);
                    }
                    catch(IOException e)
                    {
                        System.out.print("[ERROR] Could parse JSON file to String.");
                    }
                    
                }
                catch(FileNotFoundException e)
                {
                    System.out.print("[ERROR] JSON file not found.");
                }
            }
        }
        else
        {
            try 
            {
                String basename = new File(this.configsDir).getName();
                String keyName = basename.substring(0, basename.lastIndexOf("."));
                InputStream is = new FileInputStream(this.configsDir);
                try
                {
                    String jsonTxt  = IOUtils.toString(is, "UTF-8");
                    JSONObject json = new JSONObject(jsonTxt);
                    this.config.put(keyName, json);
                }
                catch(IOException e)
                {
                    System.out.print("[ERROR] Could parse filename to string");
                }
                
            }
            catch(FileNotFoundException e)
            {
                System.out.print("[ERROR] Config file not found");
            }
        }
    }

    @Override
    public InputSource resolveEntity(String publicId, String systemId) throws SAXException, IOException {
        if (systemId.contains("raml20.dtd")) {
            return new InputSource(new StringReader(""));
        }
        return null;
    }

    @Override
    public void startDocument() throws SAXException
    {
        this.startTime = LocalDateTime.now();
    }

    @Override
    public void endDocument() throws SAXException
    {
        LocalDateTime endTime = LocalDateTime.now();
        int delta = (int) ChronoUnit.SECONDS.between(this.startTime, endTime);
        System.out.println(String.format("----- FINISH PARSING: %-30s DURATION: %-15s -----", this.fileName, formatTimeDelta(delta)));
        
        ArrayList<String> tmpfileList = new ArrayList<String>();
        
        for(String tech : this.techFileList.keySet())
        {
            if(!tmpfileList.contains(this.techFileList.get(tech).get("fileName")))
            {
                try
                {
                    File f = new File(this.techFileList.get(tech).get("fileName"));
                    FileWriter fw = new FileWriter(f, true);
                    fw.write(this.footer);
                    fw.close();
                }
                catch(Exception e)
                {
                    System.out.println(String.format("[ERROR] Couldn't write footer in file %s: %s", this.footer, e));
                }
                tmpfileList.add(this.techFileList.get(tech).get("fileName"));
            }
        }
    }

    @Override
    public void startElement(String uri, String localName, String qName, Attributes attributes) throws SAXException
    {
        if(this.startElements.contains(qName))
        {
            this.readHeader = true;
            this.header += String.format("<%s", qName);
            if(qName != "raml")
            {
                for(int i = 0; i < attributes.getLength(); i++)
                {
                    this.header += String.format(" %s=\"%s\"", attributes.getLocalName(i), attributes.getValue(i));
                }
            }
            this.header += ">";
        } 
        else if(qName == "managedObject")
        {
            this.readHeader = false;
            boolean flushed = true;
            try
            {
                Matcher m = this.techRegex.matcher(attributes.getValue("distName"));
                if(m.matches())
                {
                    this.tech = m.group("tech");
                    for(String configFile : this.config.keySet())
                    {
                        if(this.config.get(configFile).keySet().contains(this.tech))
                        {
                            flushed = false;
                            this.toWrite = String.format("<%s", qName);
                            for(int i = 0; i < attributes.getLength(); i++)
                            {
                                this.toWrite += String.format(" %s=\"%s\"", attributes.getLocalName(i), attributes.getValue(i));
                            }
                            this.toWrite += ">\n";
                            this.configFile = configFile;
                            this.distName = attributes.getValue("distName");
                            break;
                        }
                    }
                }
                
            }
            catch(IllegalStateException e)
            {
                System.out.printf("[FLUSHED] %s;%s;%s\n", attributes.getValue("class"), attributes.getValue("distName"), this.fileName);
                this.toWrite = "";
            }

            if(flushed && this.verbose)
            {
                System.out.println(String.format("[FLUSHED] %s;%s", this.tech, this.distName));
                this.toWrite = "";
            }
        }
        else if(this.startElementsInner.contains(qName))
        {
            if(this.toWrite != "")
            {
                this.toWrite += String.format("<%s", qName);
                for(int i = 0; i < attributes.getLength(); i++)
                {
                    this.toWrite += String.format(" %s=\"%s\"", attributes.getLocalName(i), attributes.getValue(i));
                }
                this.toWrite += ">";
            }
        }
    }

    @Override
    public void endElement(String uri, String localName, String qName) throws SAXException {
        if(this.endElements.contains(qName) && this.toWrite != "")
        {
            this.toWrite += String.format("</%s>\n", qName);
            if(qName.equals("managedObject"))
            {
                if(!this.techFileList.containsKey(this.tech))
                {
                    HashMap<String,String> dict = new HashMap<String,String>();
                    dict.put("fileName", String.format("%s%s_%s", this.outDir, this.configFile, this.fileName));
                    // TODO: try with a buffer
                    this.techFileList.put(this.tech, dict);
                    if(!this.fileList.contains(this.techFileList.get(this.tech).get("fileName")))
                    {
                        this.fileList.add(this.techFileList.get(this.tech).get("fileName"));
                        File tmpFile = new File(this.techFileList.get(this.tech).get("fileName"));
                        if(tmpFile.exists())
                        {
                            System.out.printf("[Warning] Removing already existing file: %s\n", new File(this.techFileList.get(this.tech).get("fileName")).getName());
                            boolean result = tmpFile.delete();
                            if(!result)
                            {
                                throw new SAXException(String.format("[ERROR] Couldn't remove already existing file: %s", tmpFile.getName()));
                            }
                        }
                        this.toWrite = String.format("%s%s", this.header, this.toWrite);
                    }
                }

                // Write data to file 
                try
                {
                    File f = new File(this.techFileList.get(this.tech).get("fileName"));
                    FileWriter fw = new FileWriter(f, true);
                    fw.write(this.toWrite);
                    fw.close();
                }
                catch(IOException e)
                {
                    System.out.println(String.format("[ERROR] Couldn't write to file %s: path is most likely a directory.", this.techFileList.get(this.tech).get("fileName")));
                }

                this.toWrite = "";
            }
        }
        else if(qName.equals("header") || qName.equals("log"))
        {
            this.header += String.format("</%s>\n", qName);
        }
        else if(qName.equals("raml") || qName.equals("cmData"))
        {
            this.footer += String.format("</%s>\n", qName);
        }
    }

    @Override
    public void characters(char[] ch, int start, int length)
    {

        String content = StringEscapeUtils.escapeXml11(new String(ch, start, length));

        if(!this.toWrite.equals("") && !Pattern.compile("^.*<\\[^>]*>$").matcher(this.toWrite).matches() && !this.header.endsWith("/>"))
        {
            if(!content.trim().equals(""))
            {
                this.toWrite += content;
            }
        }
        else if(!this.header.equals("") && this.readHeader)
        {
            if(!content.trim().equals(""))
            {
                this.header += content;
            }
        }
    }

    public static String formatTimeDelta(int time)
    {
        int hours = time / (60 * 60);
        int rem = time - (hours * 60 * 60);
        int minutes = rem / 60;
        int seconds = rem % 60;

        return String.format("%02d:%02d:%02d", hours, minutes, seconds);
    }
}
