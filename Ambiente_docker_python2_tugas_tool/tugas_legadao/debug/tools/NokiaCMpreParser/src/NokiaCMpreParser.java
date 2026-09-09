import java.util.regex.Pattern;
import javax.xml.parsers.*;
import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.lang3.StringUtils;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;

public class NokiaCMpreParser {

    public static void main(String args[]) throws Exception
    {
        Options options = new Options();

        /* --indir option */
        Option indirOption = new Option("i", "indir", true, "The input directory");
        indirOption.setRequired(true);
        options.addOption(indirOption);

        /* --outdir option */
        Option outdirOption = new Option("o", "outdir", true, "The output directory");
        outdirOption.setRequired(true);
        options.addOption(outdirOption);

        /* --config option */
        Option configOption = new Option("c", "config", true, "Config file");
        configOption.setRequired(false);
        options.addOption(configOption);
        
        /* --verbose option */
        Option verboseOption = new Option("v", "verbose", true, "Verbose (v,vv)");
        verboseOption.setRequired(false);
        options.addOption(verboseOption);

        CommandLineParser cliParser = new DefaultParser();
        HelpFormatter formatter = new HelpFormatter();
        CommandLine cmd = null;

        try
        {
            cmd = cliParser.parse(options, args);
        }
        catch(Exception e)
        {
            System.out.println(e.getMessage());
            formatter.printHelp("java -jar NokiaCMPreParser.jar -indir <dir> -outdir <dir> -config <file> -verbose <v/vv>", options);
            System.exit(1);
        }

        String indirValue = cmd.getOptionValue("indir");
        String outdirValue = cmd.getOptionValue("outdir");
        String configValue = cmd.getOptionValue("config");
        String verboseValue = cmd.getOptionValue("verbose");

        /* Parsing verbose option */
        boolean verbose = false;
        if(verboseValue != null && Pattern.compile("^vv+$").matcher(verboseValue).matches())
        {
            verbose = true;
        }

        /* Parsing indir option */
        if(indirValue != null && !Files.isDirectory(Paths.get(indirValue)))
        {
            System.out.println(String.format("[CRITICAL] Input directory doesn't exists: %s", indirValue));
            System.exit(0);
        }

        /* Parsing outdir option */
        if(outdirValue != null && !Files.isDirectory(Paths.get(outdirValue)))
        {
            System.out.println(String.format("[CRITICAL] Output directory doesn't exists: %s", outdirValue));
            System.exit(0);
        }

        /* Parsing config option */
        if(configValue == null)
        {
            configValue = "";
        }
        else if(configValue != null && !Files.exists(Paths.get(configValue)))
        {
            System.out.println(String.format("[CRITICAL] Configuration file doesn't exists: %s", configValue));
            System.exit(0);
        }
        
        DateTimeFormatter dtf = DateTimeFormatter.ofPattern("dd-MM-yyyy HH:mm:ss");
        LocalDateTime startTime = LocalDateTime.now();

        /* Script output */
        System.out.println("------------------------------------------------------------------------------------");
        System.out.println(String.format("--------- SCRIPT START                -----> %s",  StringUtils.rightPad(dtf.format(startTime)+" ", 39, "-")));
        System.out.println(String.format("--------- IN DIRECTORY: %s", StringUtils.rightPad(indirValue, 60, '-')));
        System.out.println(String.format("--------- OUTPUT DIRECTORY: %s", StringUtils.rightPad(outdirValue, 56, '-')));
        
        if(configValue != "")
        {
            System.out.println(String.format("--------- CONFIG FILE: %s", StringUtils.rightPad(configValue, 61, "-")));
        }
        System.out.println("------------------------------------------------------------------------------------");

        File dir = new File(indirValue);
        String[] filesToProcess = dir.list();
        
        for(String fileName : filesToProcess)
        {
            fileName = indirValue + fileName;
            
            if(!fileName.endsWith(".xml"))
            {
                System.out.println(String.format("[WARNING] Unknown file type: %s", new File(fileName).getName()));
                continue;
            }

            System.out.println(String.format("----- START PARSING: %-31s TIME: %-10s -----", new File(fileName).getName(), dtf.format(startTime)));

            /* Parse file using SAX Parser and our brand new NokiaCMPreParserHandler */
            try
            {
                File inputFile = new File(fileName);
                SAXParserFactory factory = SAXParserFactory.newInstance();
                SAXParser saxParser = factory.newSAXParser();
                NokiaCMpreParserHandler nokiaPreParser = new NokiaCMpreParserHandler(inputFile.getName(), outdirValue, configValue, verbose);
                saxParser.parse(inputFile, nokiaPreParser);
            }
            catch(FileNotFoundException e)
            {
                System.out.println(e);
            }
        }

        /* Finished processing files */
        LocalDateTime endTime = LocalDateTime.now();
        int delta = (int) ChronoUnit.SECONDS.between(startTime, endTime);
        System.out.println("------------------------------------------------------------------------------------");
        System.out.println(String.format("--------- SCRIPT END                  -----> %30s", StringUtils.rightPad(dtf.format(endTime)+" ", 39, "-")));
        System.out.println(String.format("--------- TOTAL DURATION              -----> %-30s", StringUtils.rightPad(NokiaCMpreParserHandler.formatTimeDelta(delta)+" ", 39, "-")));
        System.out.println("------------------------------------------------------------------------------------");
    }
}
