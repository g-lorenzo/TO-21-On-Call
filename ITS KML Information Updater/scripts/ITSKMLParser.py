from lxml import etree
import bs4
import re
import time


# MAINTENANCE FUNCTIONS

def sortchildrenby(parent, attr):
    parent[:] = sorted(parent, key=lambda child: child[0].__getattribute__(attr))
    return (parent)


""" KML NAMESPACE INFORMATION
xmlns:atom="http://www.w3.org/2005/Atom"
xmlns:kml="http://www.opengis.net/kml/2.2"
xmlns:gx="http://www.google.com/kml/ext/2.2"
xmlns="http://www.opengis.net/kml/2.2"
"""

xmlns = "http://www.opengis.net/kml/2.2"
encoded_parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')


class Device:  # A class for devices with basic information. Must be initialized with device name and folder in KML

    def __init__(self, folder, name):  # Initialize with folder and name and allow for additional attributes
        self.folder = folder
        self.name = name
        self.lat = ''
        self.lon = ''
        self.mp = ''
        self.project = ''
        self.piNum = ''
        self.locat = ''
        self.dType = ''
        self.desc = ''
        self.fpi = ''
        self.crit = ''
        self.mic = ''

    def checkForDevice(self, kmlFile):
        tree = etree.parse(kmlFile, encoded_parser)  # Get the tree element which is essentially the KML file container
        root = tree.getroot(); del tree

        xpathString = self.getXpathStringForNameElement()
        device_element = root.xpath(xpathString, namespaces={"kml": xmlns})
        de_len = len(device_element); del device_element

        if de_len == 1:
            return (True)
        elif de_len > 1:
            print("WARNING: DEVICE {} has more than one instance".format(self.name))
            return (True)
        else:
            return (False)

    def createKMLElementUsingLXML(self, kmlFile): #Should this fn create text or just create an element? (Text probs necessary for correct indenting)
        Placemark = etree.Element('Placemark')

        Placemark.append(etree.Element('name'))
        Placemark.append(etree.Element('Snippet'))
        Placemark.append(etree.Element('description'))
        Placemark.append(etree.Element('LookAt'))
        Placemark.append(etree.Element('styleUrl'))
        Placemark.append(etree.Element('ExtendedData'))
        Placemark.append(etree.Element('Point'))

        Placemark[3].append(etree.Element('longitude'))
        Placemark[3].append(etree.Element('latitude'))
        Placemark[3].append(etree.Element('altitude'))
        Placemark[3].append(etree.Element('heading'))
        Placemark[3].append(etree.Element('tilt'))
        Placemark[3].append(etree.Element('range'))
        Placemark[3].append(etree.Element('altitudeMode'))

        Placemark[6].append(etree.Element('coordinates'))

        Placemark[0].text = self.name
        Placemark[1].set('maxLines', '0')
        Placemark[2].text = etree.CDATA(createCData(self))
        Placemark[3][0].text = str(self.lon)    #Longitude
        Placemark[3][1].text = str(self.lon)    #Latitude
        Placemark[3][2].text = '0'              #Altitude
        Placemark[3][3].text = '0'              #Heading
        Placemark[3][4].text = '0'              #Tilt
        Placemark[3][5].text = '1000'           #Range
        Placemark[3][6].text = 'relativeToGround'#AltitudeMode

        Placemark[6][0].text = "{},{},0".format(self.lon, self.lat) #coordinates
        Placemark[4].text = getFolderStyleMapID(kmlFile, self.folder)

        #TODO: Create text from the Placemark element; add in spaces as necessary for tabbing

    def createKMLTextFromDevice(self, kmlFile): # TODO: Update to provide proper formatting (proper indents for each element)
        soup = bs4.BeautifulSoup(features="lxml-xml")

        # Create the first layer under the <Placemark> tag
        soup.append(soup.new_tag('Placemark'))
        soup.Placemark.append(soup.new_tag('name'))
        soup.Placemark.append(soup.new_tag('Snippet'))
        soup.Placemark.append(soup.new_tag('description'))
        soup.Placemark.append(soup.new_tag('LookAt'))
        soup.Placemark.append(soup.new_tag('styleUrl'))
        soup.Placemark.append(soup.new_tag('ExtendedData'))
        soup.Placemark.append(soup.new_tag('Point'))

        # Create the second layer under the <Placemark> tag
        soup.Placemark.LookAt.append(soup.new_tag('longitude'))
        soup.Placemark.LookAt.append(soup.new_tag('latitude'))
        soup.Placemark.LookAt.append(soup.new_tag('altitude'))
        soup.Placemark.LookAt.append(soup.new_tag('heading'))
        soup.Placemark.LookAt.append(soup.new_tag('tilt'))
        soup.Placemark.LookAt.append(soup.new_tag('range'))
        soup.Placemark.LookAt.append(soup.new_tag('altitudeMode'))

        soup.Placemark.Point.append(soup.new_tag('coordinates'))

        # Add data from the device
        soup.find('name').string = self.name  # Note: This inadv. adds self.name to soup.text
        soup.find('Snippet')['maxLines'] = "0"
        soup.find('description').string = bs4.CData(createCData(self))
        soup.find('longitude').string = str(self.lon)
        soup.find('latitude').string = str(self.lat)
        soup.find('altitude').string = "0"
        soup.find('heading').string = "0"
        soup.find('tilt').string = "0"
        soup.find('range').string = "1000"
        soup.find('altitudeMode').string = "relativeToGround"

        soup.find('coordinates').string = "{},{},0".format(self.lon, self.lat)
        soup.find('styleUrl').string = getFolderStyleMapID(kmlFile, self.folder)

        return (soup.prettify())

    def getDescriptionText(self, kmlFile, xmlns):  # Find the related <description> tag and return the text

        desc_tag_name = '{' + xmlns + '}description'
        devElement = getDeviceElement(kmlFile, self)
        devParent = devElement.getparent()
        del devElement

        descElement = devParent.findall(desc_tag_name)

        if len(descElement) > 0:
            descElementText = descElement[0].text
        else:
            descElementText = ''
        del devParent, descElement

        return (descElementText)

    def getElement(self, kmlFile):  # Get an element using the getXpathString() method

        tree = etree.parse(kmlFile, encoded_parser)  # Get the tree element which is essentially the KML file container
        root = tree.getroot()

        xpathString = self.getXpathStringForNameElement()

        device_element = root.xpath(xpathString, namespaces={"kml": xmlns})

        device_element = device_element[0]

        del tree, root, xpathString

        return (device_element)

    def getXpathStringForNameElement(self):  # Get the xpath string for lxml to find the desired element in the KML
        if self.folder.find('-') != -1:
            xpath_string = '//kml:name[. ="{}"]'.format(self.name)
        else:
            xpath_string = '//kml:Folder/kml:Placemark/kml:name[. = "{}"]'.format(self.name)
        return (xpath_string)

    def printDeviceInfo(self):
        print('Name: {}'.format(self.name))
        print('Folder: {}'.format(self.folder))
        print('Description: {}'.format(self.desc))
        print('Location: {}'.format(self.locat))
        print('Latitude: {}'.format(self.lat))
        print('Longitude: {}'.format(self.lon))
        print('Milepost: {}'.format(self.mp))
        print('Project: {}'.format(self.project))
        print('P.I.#: {}'.format(self.piNum))
        print('Device Type: {}'.format(self.dType))

    def showMissingInfo(self):  # Find out which values a device does not yet have
        array = [False, False, False, False, False, False, False, False]
        for i in range(len(self.__dict__) - 2):
            if self.lat != '':
                array[i] = True
            elif self.lon != '':
                array[i] = True
            elif self.mp != '':
                array[i] = True
            elif self.project != '':
                array[i] = True
            elif self.piNum != '':
                array[i] = True
            elif self.locat != '':
                array[i] = True
            elif self.dType != '':
                array[i] = True
            elif self.desc != '':
                array[i] = True
        return (array)

    def updateWithElement(self, dev2):  # Use one element to update another

        # If dev2 has an attribute, replace dev.attribute with dev2.attribute
        if self.lat == '':
            self.lat = dev2.lat
            update = True

        if self.lon == '':
            self.lon = dev2.lon
            update = True

        if self.mp == '':
            self.mp = dev2.mp
            update = True

        if self.project == '':
            self.project = dev2.project
            update = True

        if self.piNum == '':
            self.piNum = dev2.piNum
            update = True

        if self.locat == '':
            self.locat = dev2.locat
            update = True

        if self.dType == '':
            self.dType = dev2.dType
            update = True

        if self.desc == '':
            self.desc = dev2.desc
            update = True

        del dev2


def addDeviceToKML(dev, kmlFile, newKML, allowWrite, replace=False):

    tree = etree.parse(kmlFile, encoded_parser)  # Get the tree element which is essentially the KML file container
    root = tree.getroot()  # Get the root which is the initiaiting KML node element

    xpath_string = r"//kml:Folder/kml:name[. = '{}']".format(dev.folder)
    name_element_list = root.xpath(xpath_string, namespaces={"kml": xmlns}); del root

    if len(name_element_list) > 1:  # Pause everything if multiple folders found in element
        raise NameError("Multiple folders with name '{}'".format(dev.folder))
    elif len(name_element_list) == 0:
        raise ValueError("Could not find specified folder '{}'".format(dev.folder))

    fe = name_element_list[0].getparent();
    del name_element_list  # Get parent folder element

    new_device_text = dev.createKMLTextFromDevice(kmlFile)  # Create string from the device based on a KML file
    #new_device_text = dev.createKMLElementUsingLXML(kmlFile)

    a = new_device_text.find('<description>')
    b = new_device_text.find('</description>')
    desc_text = new_device_text[a:b]
    desc_text = desc_text.replace('\n', '')
    desc_text = desc_text.replace('\t', '')

    new_device_text = new_device_text.replace(new_device_text[a:b], desc_text)
    a = new_device_text.find('<Placemark>')
    new_device_text = new_device_text[a:]
    del a, desc_text

    new_device_element = etree.fromstring(new_device_text)  # Create element from returned string
    del new_device_text

    if replace:
        old_element = fe.xpath(dev.getXpathStringForNameElement(), namespaces={"kml": xmlns})
        old_element = old_element[0].getparent()

        fe.replace(old_element, new_device_element)
        del old_element
    else:
        fe.insert(2, new_device_element)

    sortedDevices = sortchildrenby(fe[1:],'text') #Alphabetize the devices in the folder
    fe[1:] = sortedDevices; del sortedDevices

    if allowWrite:
        tree.write(newKML)

    del tree, fe, new_device_element


def compareDevices(kmlDev: Device, excelDev: Device, printUpdates):  # Find discrepancieas between devices

    if kmlDev.lat != excelDev.lat:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.lat, excelDev.lat))
    if kmlDev.lon != excelDev.lon:
        if printUpdates:
            print('Longitude -- KML: {} -- Excel: {}'.format(kmlDev.lon, excelDev.lon))
    if kmlDev.mp != excelDev.mp:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.mp, excelDev.mp))
    if kmlDev.project != excelDev.project:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.project, excelDev.project))
    if kmlDev.piNum != excelDev.piNum:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.piNum, excelDev.piNum))
    if kmlDev.locat != excelDev.locat:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.locat, excelDev.locat))
    if kmlDev.dType != excelDev.dType:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.dType, excelDev.dType))
    if kmlDev.desc != excelDev.desc:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.desc, excelDev.desc))
    if kmlDev.fpi != excelDev.fpi:
        if printUpdates:
            print('Latitude -- KML: {} -- Excel: {}'.format(kmlDev.fpi, excelDev.fpi))

    del kmlDev, excelDev


def countDevicesInFolder(kmlName, fol=''):
    if fol == '':  # If no value entered for fol, print the results for all folders
        tree = etree.parse(kmlName, encoded_parser)  # Get the tree element which is essentially the KML file container
        root = tree.getroot()  # Get the root which is the initiaiting KML node element

        xmlns = "http://www.opengis.net/kml/2.2"
        xpath_string = r"//kml:Folder"

        try:
            device_element = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Find using folder and name
            device_element = device_element[0]
        except:
            raise LookupError("No Folders Found")

    # TODO: Finish coding this section for counting the number of devvices in a folder
    # TODO: Use text from function removeDuplicatesFromKML, it's 50% of what's needed


def createCData(dev: Device, format='tbl'):
    if format == 'tbl':

        text = open(r'..\schema\table_data_ex.xml')
        newCData = text.read()

        newCData = newCData.replace('*NAME', dev.name)
        newCData = newCData.replace('*TYPE', dev.folder)
        newCData = newCData.replace('*LAT', str(dev.lat))
        newCData = newCData.replace('*LON', str(dev.lon))
        newCData = newCData.replace('*DESC', dev.desc)  # Likely empty string ''
        newCData = newCData.replace('*LOC', dev.locat)
        newCData = newCData.replace('*MP', str(dev.mp))
        newCData = newCData.replace('*PName', dev.project)
        newCData = newCData.replace('*PI', str(dev.piNum))

    elif format == 'par':
        text = open(r'..\schema\par_data_ex.xml')
        newCData = text.read()
        text.close()

        newCData = newCData.replace('*LOC', dev.locat)
        newCData = newCData.replace('*MP', dev.mp)
        newCData = newCData.replace('*DESC', dev.desc)
        newCData = newCData.replace('*PName', dev.project)
        newCData = newCData.replace('*PI', dev.piNum)

        try:
            newCData = newCData.replace('*FPI', dev.fpi)
        except:
            newCData = newCData.replace('*FPI', '')

        try:
            newCData = newCData.replace('*CRIT', dev.crit)
        except:
            newCData = newCData.replace('*CRIT', '')

        try:
            newCData = newCData.replace('*MIC', dev.mic)
        except:
            newCData = newCData.replace('*MIC', '')
    else:
        raise ValueError('Invalid format for CData')
    return (newCData)


def customUpdate(kmlDev: Device, excelDev: Device, updateFlags):
    numAttributes = 9

    if len(updateFlags) != numAttributes:
        raise IndexError("Length of updateFlags is incorrect. Current Length ({}) should"
                         " be {}".format(len(updateFlags), numAttributes))

    if updateFlags[0]:
        kmlDev.lat = excelDev.lat

    if updateFlags[1]:
        kmlDev.lon = excelDev.lon

    if updateFlags[2]:
        kmlDev.mp = excelDev.mp

    if updateFlags[3]:
        kmlDev.project = excelDev.project

    if updateFlags[4]:
        kmlDev.piNum = excelDev.piNum

    if updateFlags[5]:
        kmlDev.locat = excelDev.locat

    if updateFlags[6]:
        kmlDev.dType = excelDev.dType

    if updateFlags[7]:
        kmlDev.desc = excelDev.desc

    if updateFlags[8]:
        kmlDev.fpi = excelDev.fpi

    return (kmlDev)


def getDeviceElement(kmlFile, dev):
    tree = etree.parse(kmlFile, encoded_parser)  # Get the tree element which is essentially the KML file container
    root = tree.getroot()  # Get the root which is the initiaiting KML node element

    xpath_string = dev.getXpathStringForNameElement()

    try:
        device_element = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Find using folder and name
        return (device_element[0])
    except:
        pass
    try:
        # Find using just name
        device_element = root.xpath(xpath_string, namespaces={"kml": xmlns})
        return (device_element[0])
    except:
        # print('Device {} could not be found in KML file'.format(dev.name))
        device_element = []
        pass
    del tree, root, xpath_string
    return (device_element)


def getExistingDeviceData(kmlName, dev: Device):  # Returns object with

    description = dev.getDescriptionText(kmlName, xmlns)
    description = description.replace('\n', '')
    description = description.replace('\t', '')

    if description.find('<table') != -1:
        dType = 'tbl'
    else:
        dType = 'par'

    if dType == 'tbl':
        soup = bs4.BeautifulSoup(description, 'html.parser')
        # soup.encode('utf-8')
        nameInDesc = soup.td.b.string

        if nameInDesc != dev.name:
            print(r'Input Name: {}\nName In Description: {}'.format(dev.name, nameInDesc))
            raise ValueError(r'Name in description text does not match provided name')

        row = soup.tr

        row = row.next_sibling.next_sibling  # LATITUDE
        dev.lat = row.td.next_sibling.text

        row = row.next_sibling  # LONGITUDE
        dev.lon = row.td.next_sibling.text

        row = row.next_sibling  # DESCRIPTION
        dev.desc = row.td.next_sibling.text

        row = row.next_sibling  # LOCATION
        dev.locat = row.td.next_sibling.text

        row = row.next_sibling  # MILE POST
        dev.mp = row.td.next_sibling.text

        row = row.next_sibling  # PROJECT NAME
        dev.project = row.td.next_sibling.text

        row = row.next_sibling  # P.I.#
        dev.piNum = row.td.next_sibling.text
    else:  # dType = 'par'
        # TODO Parse existing 'par' format data to get attributes
        soup = bs4.BeautifulSoup(description, features='lxml-xml')

    return (dev)


def getFolderStyleMapID(kmlName, folder):
    try:
        tree = etree.parse(kmlName, encoded_parser)  # Get the tree element which is essentially the KML file container
        root = tree.getroot()  # Get the root which is the initiaiting KML node element

        xpath_string = r"//kml:Document/kml:Folder/kml:name[. = '{}']".format(folder)
        name_element = root.xpath(xpath_string, namespaces={"kml": xmlns})
        fe = name_element[0].getparent()
        first_device = fe.find('{http://www.opengis.net/kml/2.2}Placemark')
        styleTag = first_device.find('{http://www.opengis.net/kml/2.2}styleUrl')

        styleMapID = styleTag.text
        del tree, root, name_element, first_device, styleTag
    except:
        styleMapID = ''
        print("Unable to find StyleMap ID for folder -- {} -- in file -- {} --".format(folder, kmlName))

    return (styleMapID)


def removeDuplicatesFromKML(kmlName, folders=''):
    tree = etree.parse(kmlName, encoded_parser)  # Get the tree element which is essentially the KML file container
    root = tree.getroot()  # Get the root which is the initiaiting KML node element

    # TODO: Check/Update first 'if' statement, is it finding correct folder using [. = '{}']?
    if (folders != '') & (type(folders) == str):  # Provided *folders* input is a string name for a single folder
        xpath_string = r"//kml:Document/kml:Folder/kml:name[. = '{}']".format(
            folders)  # *NOTE* This produces NAME element
        folder_element_list = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Find using folder and name

    elif folders == '':  # Provided *folders* input is not given
        xpath_string = r"//kml:Document/kml:Folder"
        folder_element_list = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Find using folder and name
        folder_element_list.remove(folder_element_list[0])  # Remove first list entry which is the Legend

    else:  # Assume it is a list
        new_element_list = []
        xpath_string = r"//kml:Document/kml:Folder"
        folder_element_list = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Find using folder and name

        for de in folder_element_list:
            dechildren = de.getchildren()
            deFirstChild = dechildren[0]

            deFirstChild = deFirstChild.text

            if deFirstChild in folders:
                new_element_list.append(de)

        folder_element_list = new_element_list
        del new_element_list

    for fe in folder_element_list:  # For each folder element

        device_element_list = fe.findall('{http://www.opengis.net/kml/2.2}Placemark')  # Find all placemark sub-elements
        de_names = [de[0].text for de in device_element_list]  # Retrieve the names of placemark elements to a list

        if len(de_names) != len(set(de_names)):  # If the list of device names contains duplicates
            for de in de_names:
                if de_names.count(de) > 1:
                    xpath_string = r"//kml:Folder[@id='{}']/kml:Placemark/kml:name[. = '{}']".format(fe[0].text, de)
                    dup_elements = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Get all duplicate elements

                    # TODO: With duplicate elements, compare attributes and combine. Delete all but one and update remaining

                    print('Folder: {} - Device: {} is a duplicate'.format(fe[0].text, de))

    print("Your file -- {} -- has been updated".format(kmlName))


def updateCData(kmlName, newCData, newKML, dev):
    tree = etree.parse(kmlName, encoded_parser)  # Get the tree element which is essentially the KML file container
    root = tree.getroot()  # Get the root which is the initiaiting KML node element

    xpath_string = r"//kml:Folder[@id='{}']/kml:Placemark/kml:name[. = '{}']".format(dev.folder, dev.name)

    try:
        device_element = root.xpath(xpath_string, namespaces={"kml": xmlns})  # Find using folder and name
        device_element = device_element[0]
    except:
        new_xpath_string = r"//kml:Folder/kml:Placemark/kml:name[. = '{}']".format(dev.name)  # Find using just name
        device_element = root.xpath(new_xpath_string, namespaces={"kml": xmlns})
        device_element = device_element[0]

    description_tag = device_element.getnext().getnext()  # move from <name> to <description> under <Placemark>
    description_tag.text = etree.CDATA(newCData)

    et = etree.ElementTree(root)
    et.write(newKML)

    # print('Device ID: {} updated successfully!'.format(dev.name))


def processSoupText(souptext, indent_space=4):
    #TODO: Add text to ***PROPERLY*** process whatever is returned from createKMLTextFromDevice() method

    a = souptext.find('<description>')
    b = souptext.find('</description>')
    desc_text = souptext[a:b]
    desc_text = desc_text.replace('\n', '')
    desc_text = desc_text.replace('\t', '')

    new_device_text = souptext.replace(souptext[a:b], desc_text)

    a = new_device_text.find('<Placemark>')
    new_device_text = new_device_text[a:]

    return(new_device_text)

def main(cam, fol, kml, new_kml, ):
    newDevice = Device(fol, cam)
    newDevice = getExistingDeviceData(kml, newDevice)

    newCData = createCData(newDevice, 'tbl')

    updateCData(kml, newCData, new_kml, newDevice)

    return ()


if __name__ == "__main__":
    import time

    kml = r"..\data\All Devices v6.0\doc.kml"
    newKML = kml.replace('doc.kml','doc_gp.kml')

    myDevice = Device('CAM', 'GDOT-CAM-GP92')
    myDevice.lat = 33.842417
    myDevice.lon = -84.359333

    for i in range(5):
        rep = True
        if i == 0:
            rep = False


        tlist = addDeviceToKML(myDevice, kml, newKML, allowWrite=True, replace=rep)