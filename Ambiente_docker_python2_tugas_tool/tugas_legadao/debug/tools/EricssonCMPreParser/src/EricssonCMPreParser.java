import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import java.nio.file.Files;
import java.nio.file.Paths;

import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;

/** 
 * Ericsson CM PreParser LF 2.0
 * 
 * LF stands for Lightning Fast
 *
 * @author <paulo-a-gil@alticelabs.com>
 *
 * "Não há soluções triviais para problemas complexos"
 * 
 */

public class EricssonCMPreParser {
    public static void main(String[] args) throws Exception
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


        /* --verbose option */
        Option verboseOption = new Option("v", "verbose", false, "Verbose");
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
            formatter.printHelp("EricssonCMPreParser.jar", options);
            System.exit(0);
        }

        String indirValue = cmd.getOptionValue("indir");
        String outdirValue = cmd.getOptionValue("outdir");

        System.out.println("##############################################################");
        System.out.println("##########       Ericsson CM PreParser LF 2.0       ##########");
        System.out.println("##############################################################");

        /* Parsing verbose option */
        boolean verbose = false;
        if(cmd.hasOption("verbose"))
        {
            verbose = true;
        }
        
        /* Parsing indir option */
        if(indirValue != null && !Files.isDirectory(Paths.get(indirValue)))
        {
            System.out.println(String.format("ERROR: Input directory doesn't exists: %s", indirValue));
            System.exit(0);
        }

        /* Parsing outdir option */
        if(outdirValue != null && !Files.isDirectory(Paths.get(outdirValue)))
        {
            System.out.println(String.format("ERROR: Output directory doesn't exists: %s", outdirValue));
            System.exit(0);
        }

        /* Checks if there is a list of previously processed files */
        File ppListFile = new File(indirValue+"preprocessed.list");
        if(!ppListFile.exists() && verbose)
        {
            System.out.println("INFO: No previous processed files detected -> Processing all files");
        }

        // Try deserialization
        PreProcessedList ppList = null;
        try
        {
            FileInputStream file = new FileInputStream(indirValue+"preprocessed.list");
            ObjectInputStream in = new ObjectInputStream(file);

            ppList = (PreProcessedList) in.readObject();

            in.close();
            file.close();
        }
        catch(IOException e)
        {
            ppList = new PreProcessedList(new ArrayList<String>());
        }
        catch(ClassNotFoundException e)
        {
            System.out.println(String.format("ERROR: Could not deserialize object -> \"%sprocessed.list\""));
        }
        

        if(verbose && ppList.getPpFiles().size() > 0)
        {
            System.out.println("\n---------------------------------------------\nPreviously processed files list:\n");
            System.out.println(String.join("\n-> ", ppList.getPpFiles()));
            System.out.println("---------------------------------------------\n");
        }

        String[] pathnames = new File(indirValue).list();

        for(String fname : pathnames)
        {
            // Check if fname is not a directory
            if(!Files.isDirectory(Paths.get(indirValue+fname)))
            {
                // Check if file has already been processed
                if(!ppList.getPpFiles().contains(fname) && ! fname.equals("preprocessed.list"))
                {
                    String fileDatetime = filenameToDatetime(fname);

                    if(fileDatetime != null)
                    {
                        try
                        {
                            File inputFile = new File(indirValue+fname);
                            SAXParserFactory factory = SAXParserFactory.newInstance();
                            SAXParser saxParser = factory.newSAXParser();
                            EricssonCMPreParserHandlerLF ericssonPreParser = new EricssonCMPreParserHandlerLF(fname, fileDatetime, outdirValue, verbose);
                            saxParser.parse(inputFile, ericssonPreParser);
                        }
                        catch(IOException e)
                        {
                            System.out.println(String.format("ERROR: Unable to process file: %s", fname));
                        }
                    }
                    else
                    {
                        if(verbose)
                        {
                            System.out.println(String.format("ERROR: Couldn't get datetime from filename: %s", fname));
                        }
                    }

                    // Add newly processed file to ppList
                    ppList.addFileToList(fname);

                    // Serialize ppList
                    try
                    {
                        FileOutputStream file = new FileOutputStream(indirValue+"preprocessed.list");
                        ObjectOutputStream out = new ObjectOutputStream(file);

                        out.writeObject(ppList);

                        out.close();
                        file.close();

                        if(verbose)
                        {
                            System.out.println("INFO: Serialization complete of \"preprocessed.list\" object");
                        }
                    }
                    catch(IOException e)
                    {
                        e.printStackTrace();
                    }
                }
                else
                {
                    if(verbose && !fname.equals("preprocessed.list"))
                    {
                        System.out.println(String.format("INFO: File has already been processed: %s", fname));
                    }
                }
            }
        }
    }

    public static String filenameToDatetime(String filename)
    {
        DateTimeFormatter inFormat = DateTimeFormatter.ofPattern("yyyyMMddHHmm");
        DateTimeFormatter outFormat = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        Matcher m = Pattern.compile("^.*?_([0-9]+).xml$").matcher(filename);
        String datematch = null;

        if(m.find())
        {
            datematch = m.group(1);
        }

        if(datematch != null)
        {
            String result = null;
            try
            {
                result = outFormat.format(inFormat.parse(datematch));
            }
            catch(DateTimeParseException e1)
            {
                try
                {
                    String dt = datematch + "0000";
                    result = outFormat.format(inFormat.parse(dt));
                }
                catch(DateTimeParseException e2)
                {
                    System.out.println("ERROR: Could not parse datetime in filename");
                }
            }
            return result;
        }
        return null;
    }
}

