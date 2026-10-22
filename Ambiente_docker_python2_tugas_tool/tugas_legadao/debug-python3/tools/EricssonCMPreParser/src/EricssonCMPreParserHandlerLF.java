import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;

import java.util.ArrayList;
import java.util.Arrays;

import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

/** 
 * Ericsson CM PreParser Handler LF 2.0
 * 
 * LF stands for Lightning Fast
 *
 * @author <paulo-a-gil@alticelabs.com>
 *
 * "Não há soluções triviais para problemas complexos"
 * 
 */

public class EricssonCMPreParserHandlerLF extends DefaultHandler {
    // Datetime formatter 
    private DateTimeFormatter dtf = DateTimeFormatter.ofPattern("dd-MM-yyyy HH:mm:ss");

    // Parse timestamp
    private LocalDateTime parseStartTime = null;

    // Store the filename for debugging purposes
    private String filename;

    // Store the filename without extension
    private String filenamePath;

    // Counts the number of generated files
    private int meContextFiles = 0;

    // Counts the number of tabs in XML tree
    private int tabs = 0;

    // Private arrays to handle header, footer and hierarchy values
    private ArrayList<String> header = new ArrayList<String>();
    private ArrayList<String> footer = new ArrayList<String>();
    private ArrayList<String> hierarchy = new ArrayList<String>();

    // File datetime
    private String datetime;

    // Output verbosity
    private boolean verbose;

    // Output directory
    private String outdir;

    public EricssonCMPreParserHandlerLF(String filename, String datetime, String outdir, boolean verbose)
    {
        this.filename = filename;
        this.datetime = datetime;
        this.outdir = outdir;
        this.verbose = verbose;

        if(!this.outdir.endsWith("/"))
        {
            this.outdir += "/";
        }

        this.filenamePath = this.filename.replace(".xml", "") + "/";
    }

    @Override
    public void startDocument() throws SAXException
    {
        if(this.parseStartTime == null)
        {
            this.parseStartTime = LocalDateTime.now();
        }
        System.out.println(String.format("[%s] Starting to process file %s", dtf.format(LocalDateTime.now()), this.filename));
    }

    @Override
    public void endDocument() throws SAXException
    {
        System.out.println(String.format("[%s] Finished processing file %s", dtf.format(LocalDateTime.now()), this.filename));
        printStats();
    }

    @Override
    public void startElement(String uri, String localName, String qname, Attributes attrs)
    {
        // Remove namespace from qname
        String[] qnameList = qname.split(":");
        String qnameNoNS = qnameList.length > 1 ? qnameList[1] : qnameList[0];
        
        if(Arrays.asList("bulkCmConfigDataFile","fileHeader","configData", "SubNetwork").contains(qnameNoNS))
        {
            String headerItem = "";
            String footerItem = "";

            // Add SubNetwork to hierarchy
            if(qnameNoNS.equals("SubNetwork"))
            {
                this.hierarchy.add(String.format("%s=%s", qnameNoNS, attrs.getValue("id")));
            }

            String termination = "";

            if(qnameNoNS.equals("fileHeader"))
            {
                headerItem += new String(new char[this.tabs]).replace("\0", "\t");
                headerItem += String.format("<%s", qname);
                termination = "/>\n";
            }
            else
            {
                headerItem += new String(new char[this.tabs]).replace("\0", "\t");
                headerItem += String.format("<%s", qname);
                termination = ">\n";
                this.tabs++;
            }
            
            // Parse qname attributes
            for(int i = 0; i < attrs.getLength(); i++)
            {
                headerItem += String.format(" %s=\"%s\"", attrs.getLocalName(i), attrs.getValue(i));
            }
            
            // Write corresponding termination
            headerItem += termination;

            // Setup footer element
            if(qnameNoNS.equals("fileHeader"))
            {
                footerItem += String.format("<%s", "fileFooter");
                footerItem += String.format(" %s=\"%s\"/>\n", "dateTime", this.datetime);
            }
            else
            {
                footerItem += String.format("</%s>\n", qname);
            }
            
            // Append to header array
            this.header.add(headerItem);

            // Append to footer array
            this.footer.add(footerItem);
        }
        else if(qnameNoNS.equals("MeContext"))
        {
            // Add MeContext to hierarchy
            String meContext = String.format("%s=%s", qnameNoNS, attrs.getValue("id"));
            this.hierarchy.add(meContext);

            // Get meContext partition filename
            String meContextFile = meContext + ".xml";

            // Get meContext final filename
            String finalFilename = String.join(",", hierarchy) + ".xml";

            if(this.verbose)
            {
                System.out.println(String.format("MC: Opening file %s", finalFilename));
            }
            
            // Write header
            try 
            {
                FileWriter fw = new FileWriter(this.outdir+finalFilename);
                fw.write(String.join("", this.header));
                fw.close();
            } catch (IOException e) {
                e.printStackTrace();
            }

            // Append files
            appendFiles(finalFilename, meContextFile);

            // Write footer
            writeFooter(finalFilename);
        }
    }

    @Override
    public void endElement(String uri, String localName, String qname) throws SAXException
    {
        // Remove namespace from qname
        String[] qnameList = qname.split(":");
        String qnameNoNS = qnameList.length > 1 ? qnameList[1] : qnameList[0];

        if(qnameNoNS.equals("SubNetwork"))
        {
            // Remove SubNetwork from header, footer and hierarchy
            this.header.remove(this.header.size()-1);
            this.footer.remove(this.footer.size()-1);
            this.hierarchy.remove(this.hierarchy.size()-1);
        }
        else if(qnameNoNS.equals("MeContext"))
        {
            // Remove meContext from hierarchy
            this.hierarchy.remove(this.hierarchy.size()-1);
            this.meContextFiles++;
        }
    }

    /* Helper methods */
    private void printStats()
    {
        System.out.println("------------------------------------------------------------------------------------");
        System.out.println(String.format("--------- Parsing Started: %s", this.dtf.format(this.parseStartTime)));
        System.out.println(String.format("--------- Parsing Finished: %s", this.dtf.format(LocalDateTime.now())));
        int delta = (int) ChronoUnit.SECONDS.between(this.parseStartTime, LocalDateTime.now());
        System.out.println(String.format("--------- Execution time: %s", formatTimeDelta(delta)));
        System.out.println("\n--------- Statistics:");
        System.out.println(String.format("--------- MeContext Files -----> %s", this.meContextFiles));
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

    private void appendFiles(String dest, String src)
    {
        try
        {
            // Create a writter for destination file
            BufferedWriter out = new BufferedWriter(new FileWriter(this.outdir+dest, true));

            // Create a reader for source file
            BufferedReader in = new BufferedReader(new FileReader(this.outdir+this.filenamePath+src));

            String str;
            while((str = in.readLine()) != null) 
            {
                out.write(str);
                out.write("\n");
            }

            // Close buffers
            in.close();
            out.close();
        }
        catch(IOException e)
        {
            e.printStackTrace();
        }
    }

    public void writeFooter(String filename)
    {
        // Prepare footer
        int footerTabs = this.footer.size()-2;
        ArrayList<String> formatedFooter = new ArrayList<String>();

        for(int i = this.footer.size() - 1; i >= 0; i--)
        {
            String item = new String(new char[footerTabs]).replace("\0", "\t");
            item += this.footer.get(i);
            formatedFooter.add(item);
            if(i != 2)
            {
                footerTabs--;
            }
        }
        
        // Write footer
        try 
        {
            FileWriter fw = new FileWriter(this.outdir+filename, true);
            fw.write(String.join("", formatedFooter));
            fw.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
