import requests
import pandas as pd
import json
import os
from typing import List, Dict, Optional, Any
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging

logger = logging.getLogger(__name__)

class PortsService:
    def __init__(self):
        self.ports_data = []
        self.ports_file = "data/world_ports.json"
        self.geolocator = Nominatim(user_agent="maritime_assistant")
        self._initialize_ports_data()
    
    def _initialize_ports_data(self):
        """Initialize ports data from multiple sources"""
        try:
            # Try to load cached data first
            if os.path.exists(self.ports_file):
                with open(self.ports_file, 'r', encoding='utf-8') as f:
                    self.ports_data = json.load(f)
                logger.info(f"Loaded {len(self.ports_data)} ports from cache")
            else:
                # Create comprehensive ports database
                self._create_comprehensive_ports_database()
        except Exception as e:
            logger.error(f"Error initializing ports data: {e}")
            self._create_fallback_ports_data()
    
    def _create_comprehensive_ports_database(self):
        """Create comprehensive ports database from multiple sources"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            logger.info("Creating comprehensive ports database...")
            
            # Initialize with known major ports data
            self.ports_data = self._get_major_ports_data()
            
            # Try to fetch additional ports from free APIs
            try:
                additional_ports = self._fetch_additional_ports()
                self.ports_data.extend(additional_ports)
            except Exception as e:
                logger.warning(f"Could not fetch additional ports: {e}")
            
            # Remove duplicates and sort
            self._deduplicate_and_sort()
            
            # Save to cache
            with open(self.ports_file, 'w', encoding='utf-8') as f:
                json.dump(self.ports_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created ports database with {len(self.ports_data)} ports")
            
        except Exception as e:
            logger.error(f"Error creating ports database: {e}")
            self._create_fallback_ports_data()
    
    def _get_major_ports_data(self) -> List[Dict]:
        """Get comprehensive list of major world ports"""
        return [
            # North America - USA
            {"name": "Port of Los Angeles", "country": "USA", "latitude": 33.7361, "longitude": -118.2645, "type": "Container", "locode": "USLAX"},
            {"name": "Port of Long Beach", "country": "USA", "latitude": 33.7553, "longitude": -118.2135, "type": "Container", "locode": "USLGB"},
            {"name": "Port of New York/New Jersey", "country": "USA", "latitude": 40.6698, "longitude": -74.0431, "type": "Container", "locode": "USNYC"},
            {"name": "Port of Savannah", "country": "USA", "latitude": 32.1345, "longitude": -81.1426, "type": "Container", "locode": "USSAV"},
            {"name": "Port of Seattle", "country": "USA", "latitude": 47.5785, "longitude": -122.3358, "type": "Container", "locode": "USSEA"},
            {"name": "Port of Houston", "country": "USA", "latitude": 29.7372, "longitude": -95.2747, "type": "Bulk/Energy", "locode": "USHOU"},
            {"name": "Port of Oakland", "country": "USA", "latitude": 37.8044, "longitude": -122.2712, "type": "Container", "locode": "USOAK"},
            {"name": "Port of Miami", "country": "USA", "latitude": 25.7741, "longitude": -80.1666, "type": "Cruise/Container", "locode": "USMIA"},
            {"name": "Port of Charleston", "country": "USA", "latitude": 32.7833, "longitude": -79.9313, "type": "Container", "locode": "USCHS"},
            {"name": "Port of Norfolk", "country": "USA", "latitude": 36.8468, "longitude": -76.2951, "type": "Container/Naval", "locode": "USNFK"},
            
            # North America - Canada
            {"name": "Port of Vancouver", "country": "Canada", "latitude": 49.2827, "longitude": -123.1207, "type": "Container/Bulk", "locode": "CAVAN"},
            {"name": "Port of Montreal", "country": "Canada", "latitude": 45.5088, "longitude": -73.5542, "type": "Container", "locode": "CAMTR"},
            {"name": "Port of Halifax", "country": "Canada", "latitude": 44.6488, "longitude": -63.5752, "type": "Container", "locode": "CAHAL"},
            {"name": "Port of Prince Rupert", "country": "Canada", "latitude": 54.3150, "longitude": -130.3209, "type": "Container/Bulk", "locode": "CAPRP"},
            
            # Europe - Netherlands
            {"name": "Port of Rotterdam", "country": "Netherlands", "latitude": 51.9225, "longitude": 4.4792, "type": "Container/Bulk", "locode": "NLRTM"},
            {"name": "Port of Amsterdam", "country": "Netherlands", "latitude": 52.3676, "longitude": 4.9041, "type": "Bulk/Liquid", "locode": "NLAMS"},
            
            # Europe - Germany
            {"name": "Port of Hamburg", "country": "Germany", "latitude": 53.5511, "longitude": 9.9937, "type": "Container", "locode": "DEHAM"},
            {"name": "Port of Bremen/Bremerhaven", "country": "Germany", "latitude": 53.5395, "longitude": 8.5809, "type": "Container", "locode": "DEBRV"},
            
            # Europe - Belgium
            {"name": "Port of Antwerp", "country": "Belgium", "latitude": 51.2194, "longitude": 4.4025, "type": "Container/Chemical", "locode": "BEANR"},
            {"name": "Port of Zeebrugge", "country": "Belgium", "latitude": 51.3273, "longitude": 3.2052, "type": "Container/RoRo", "locode": "BEZEE"},
            
            # Europe - UK
            {"name": "Port of London", "country": "United Kingdom", "latitude": 51.5074, "longitude": -0.1278, "type": "Container/General", "locode": "GBLON"},
            {"name": "Port of Southampton", "country": "United Kingdom", "latitude": 50.9097, "longitude": -1.4044, "type": "Container/Cruise", "locode": "GBSOU"},
            {"name": "Port of Felixstowe", "country": "United Kingdom", "latitude": 51.9613, "longitude": 1.3511, "type": "Container", "locode": "GBFXT"},
            {"name": "Port of Liverpool", "country": "United Kingdom", "latitude": 53.4084, "longitude": -2.9916, "type": "Container", "locode": "GBLIV"},
            
            # Europe - Spain
            {"name": "Port of Valencia", "country": "Spain", "latitude": 39.4699, "longitude": -0.3763, "type": "Container", "locode": "ESVLC"},
            {"name": "Port of Barcelona", "country": "Spain", "latitude": 41.3851, "longitude": 2.1734, "type": "Container/Cruise", "locode": "ESBCN"},
            {"name": "Port of Algeciras", "country": "Spain", "latitude": 36.1328, "longitude": -5.4503, "type": "Container", "locode": "ESALG"},
            
            # Europe - Italy
            {"name": "Port of Genoa", "country": "Italy", "latitude": 44.4056, "longitude": 8.9463, "type": "Container", "locode": "ITGOA"},
            {"name": "Port of La Spezia", "country": "Italy", "latitude": 44.1057, "longitude": 9.8281, "type": "Container", "locode": "ITLSP"},
            {"name": "Port of Naples", "country": "Italy", "latitude": 40.8518, "longitude": 14.2681, "type": "Container/Ferry", "locode": "ITNAL"},
            
            # Europe - France
            {"name": "Port of Le Havre", "country": "France", "latitude": 49.4944, "longitude": 0.1079, "type": "Container", "locode": "FRLEH"},
            {"name": "Port of Marseille", "country": "France", "latitude": 43.2965, "longitude": 5.3698, "type": "Container/Cruise", "locode": "FRMRS"},
            
            # Europe - Nordic Countries
            {"name": "Port of Copenhagen", "country": "Denmark", "latitude": 55.6761, "longitude": 12.5683, "type": "Container/Ferry", "locode": "DKCPH"},
            {"name": "Port of Gothenburg", "country": "Sweden", "latitude": 57.7089, "longitude": 11.9746, "type": "Container", "locode": "SEGOT"},
            {"name": "Port of Helsinki", "country": "Finland", "latitude": 60.1699, "longitude": 24.9384, "type": "Container/Ferry", "locode": "FIHEL"},
            {"name": "Port of Oslo", "country": "Norway", "latitude": 59.9139, "longitude": 10.7522, "type": "Container/Ferry", "locode": "NOOSL"},
            {"name": "Port of Stockholm", "country": "Sweden", "latitude": 59.3293, "longitude": 18.0686, "type": "Container/Ferry", "locode": "SESTO"},
            
            # Asia - China
            {"name": "Port of Shanghai", "country": "China", "latitude": 31.2304, "longitude": 121.4737, "type": "Container", "locode": "CNSHA"},
            {"name": "Port of Ningbo", "country": "China", "latitude": 29.8683, "longitude": 121.5440, "type": "Container/Bulk", "locode": "CNNGB"},
            {"name": "Port of Shenzhen", "country": "China", "latitude": 22.5431, "longitude": 114.0579, "type": "Container", "locode": "CNSZX"},
            {"name": "Port of Guangzhou", "country": "China", "latitude": 23.1291, "longitude": 113.2644, "type": "Container", "locode": "CNGZH"},
            {"name": "Port of Qingdao", "country": "China", "latitude": 36.0986, "longitude": 120.3719, "type": "Container", "locode": "CNTAO"},
            {"name": "Port of Tianjin", "country": "China", "latitude": 39.1012, "longitude": 117.7011, "type": "Container", "locode": "CNTXG"},
            {"name": "Port of Xiamen", "country": "China", "latitude": 24.4798, "longitude": 118.0894, "type": "Container", "locode": "CNXMN"},
            {"name": "Port of Dalian", "country": "China", "latitude": 38.9140, "longitude": 121.6147, "type": "Container/Bulk", "locode": "CNDLC"},
            {"name": "Port of Hong Kong", "country": "Hong Kong", "latitude": 22.2783, "longitude": 114.1747, "type": "Container", "locode": "HKHKG"},
            
            # Asia - Singapore
            {"name": "Port of Singapore", "country": "Singapore", "latitude": 1.2966, "longitude": 103.8006, "type": "Container/Transshipment", "locode": "SGSIN"},
            
            # Asia - Japan
            {"name": "Port of Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503, "type": "Container", "locode": "JPTYO"},
            {"name": "Port of Yokohama", "country": "Japan", "latitude": 35.4437, "longitude": 139.6380, "type": "Container", "locode": "JPYOK"},
            {"name": "Port of Osaka", "country": "Japan", "latitude": 34.6937, "longitude": 135.5023, "type": "Container", "locode": "JPOSA"},
            {"name": "Port of Kobe", "country": "Japan", "latitude": 34.6901, "longitude": 135.1956, "type": "Container", "locode": "JPUKB"},
            {"name": "Port of Nagoya", "country": "Japan", "latitude": 35.1815, "longitude": 136.9066, "type": "Container/Auto", "locode": "JPNGO"},
            
            # Asia - South Korea
            {"name": "Port of Busan", "country": "South Korea", "latitude": 35.1796, "longitude": 129.0756, "type": "Container", "locode": "KRPUS"},
            {"name": "Port of Incheon", "country": "South Korea", "latitude": 37.4563, "longitude": 126.7052, "type": "Container", "locode": "KRICN"},
            {"name": "Port of Ulsan", "country": "South Korea", "latitude": 35.5384, "longitude": 129.3114, "type": "Industrial/Bulk", "locode": "KRULS"},
            
            # Asia - Southeast Asia
            {"name": "Port of Port Klang", "country": "Malaysia", "latitude": 3.0044, "longitude": 101.3925, "type": "Container", "locode": "MYPKG"},
            {"name": "Port of Tanjung Pelepas", "country": "Malaysia", "latitude": 1.3644, "longitude": 103.5494, "type": "Container", "locode": "MYTPP"},
            {"name": "Port of Bangkok", "country": "Thailand", "latitude": 13.7563, "longitude": 100.5018, "type": "Container", "locode": "THBKK"},
            {"name": "Port of Laem Chabang", "country": "Thailand", "latitude": 13.0827, "longitude": 100.8833, "type": "Container", "locode": "THLCH"},
            {"name": "Port of Ho Chi Minh City", "country": "Vietnam", "latitude": 10.7769, "longitude": 106.7009, "type": "Container", "locode": "VNSGN"},
            {"name": "Port of Haiphong", "country": "Vietnam", "latitude": 20.8449, "longitude": 106.6881, "type": "Container", "locode": "VNHPH"},
            {"name": "Port of Manila", "country": "Philippines", "latitude": 14.5995, "longitude": 120.9842, "type": "Container", "locode": "PHMNL"},
            {"name": "Port of Jakarta", "country": "Indonesia", "latitude": -6.2088, "longitude": 106.8456, "type": "Container", "locode": "IDJKT"},
            
            # Asia - India
            {"name": "Port of Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777, "type": "Container", "locode": "INNSA"},
            {"name": "Port of Chennai", "country": "India", "latitude": 13.0827, "longitude": 80.2707, "type": "Container", "locode": "INMAA"},
            {"name": "Port of Kolkata", "country": "India", "latitude": 22.5726, "longitude": 88.3639, "type": "Container", "locode": "INCCU"},
            {"name": "Port of Cochin", "country": "India", "latitude": 9.9312, "longitude": 76.2673, "type": "Container/Transshipment", "locode": "INCOK"},
            {"name": "Port of Visakhapatnam", "country": "India", "latitude": 17.6868, "longitude": 83.2185, "type": "Bulk/Container", "locode": "INVTZ"},
            {"name": "Port of Kandla", "country": "India", "latitude": 23.0225, "longitude": 70.2208, "type": "Bulk", "locode": "INKDL"},
            
            # Middle East
            {"name": "Port of Dubai", "country": "UAE", "latitude": 25.2854, "longitude": 55.3209, "type": "Container/Transshipment", "locode": "AEDXB"},
            {"name": "Port of Abu Dhabi", "country": "UAE", "latitude": 24.4539, "longitude": 54.3773, "type": "Container", "locode": "AEAUH"},
            {"name": "Port of Jebel Ali", "country": "UAE", "latitude": 25.0118, "longitude": 55.1370, "type": "Container", "locode": "AEJEA"},
            {"name": "Port of King Abdullah", "country": "Saudi Arabia", "latitude": 22.4667, "longitude": 39.1833, "type": "Container", "locode": "SAKAC"},
            {"name": "Port of Jeddah", "country": "Saudi Arabia", "latitude": 21.5429, "longitude": 39.1728, "type": "Container", "locode": "SAJED"},
            {"name": "Port of Kuwait", "country": "Kuwait", "latitude": 29.3375, "longitude": 47.6581, "type": "Container", "locode": "KWKWI"},
            {"name": "Port of Doha", "country": "Qatar", "latitude": 25.2867, "longitude": 51.5333, "type": "Container", "locode": "QADOH"},
            {"name": "Port of Salalah", "country": "Oman", "latitude": 17.0151, "longitude": 54.0924, "type": "Container/Transshipment", "locode": "OMSLL"},
            
            # Africa - North Africa
            {"name": "Port of Alexandria", "country": "Egypt", "latitude": 31.2001, "longitude": 29.9187, "type": "Container", "locode": "EGALY"},
            {"name": "Port Said", "country": "Egypt", "latitude": 31.2653, "longitude": 32.3020, "type": "Container/Transshipment", "locode": "EGPSD"},
            {"name": "Port of Casablanca", "country": "Morocco", "latitude": 33.5731, "longitude": -7.5898, "type": "Container", "locode": "MACAS"},
            {"name": "Port of Tangier Med", "country": "Morocco", "latitude": 35.8781, "longitude": -5.4078, "type": "Container/Transshipment", "locode": "MATNG"},
            {"name": "Port of Tunis", "country": "Tunisia", "latitude": 36.8065, "longitude": 10.1815, "type": "Container", "locode": "TNTUN"},
            
            # Africa - West Africa
            {"name": "Port of Lagos", "country": "Nigeria", "latitude": 6.4474, "longitude": 3.3903, "type": "Container", "locode": "NGLOS"},
            {"name": "Port of Tema", "country": "Ghana", "latitude": 5.6667, "longitude": -0.0167, "type": "Container", "locode": "GHTEM"},
            {"name": "Port of Abidjan", "country": "Ivory Coast", "latitude": 5.3364, "longitude": -4.0267, "type": "Container", "locode": "CIABJ"},
            {"name": "Port of Dakar", "country": "Senegal", "latitude": 14.7167, "longitude": -17.4677, "type": "Container", "locode": "SNDKR"},
            
            # Africa - East Africa
            {"name": "Port of Djibouti", "country": "Djibouti", "latitude": 11.5720, "longitude": 43.1456, "type": "Container/Transshipment", "locode": "DJJIB"},
            {"name": "Port of Mombasa", "country": "Kenya", "latitude": -4.0435, "longitude": 39.6682, "type": "Container", "locode": "KEMBA"},
            {"name": "Port of Dar es Salaam", "country": "Tanzania", "latitude": -6.7924, "longitude": 39.2083, "type": "Container", "locode": "TZDAR"},
            
            # Africa - South Africa
            {"name": "Port of Durban", "country": "South Africa", "latitude": -29.8587, "longitude": 31.0218, "type": "Container", "locode": "ZADUR"},
            {"name": "Port of Cape Town", "country": "South Africa", "latitude": -33.9249, "longitude": 18.4241, "type": "Container", "locode": "ZACPT"},
            {"name": "Port Elizabeth", "country": "South Africa", "latitude": -33.9608, "longitude": 25.6022, "type": "Container/Auto", "locode": "ZAPLZ"},
            
            # South America - Brazil
            {"name": "Port of Santos", "country": "Brazil", "latitude": -23.9537, "longitude": -46.3334, "type": "Container", "locode": "BRSSZ"},
            {"name": "Port of Rio de Janeiro", "country": "Brazil", "latitude": -22.9068, "longitude": -43.1729, "type": "Container", "locode": "BRRIO"},
            {"name": "Port of Paranagua", "country": "Brazil", "latitude": -25.5198, "longitude": -48.5089, "type": "Bulk", "locode": "BRPNG"},
            {"name": "Port of Itajai", "country": "Brazil", "latitude": -26.9077, "longitude": -48.6658, "type": "Container", "locode": "BRITJ"},
            
            # South America - Other Countries
            {"name": "Port of Callao", "country": "Peru", "latitude": -12.0464, "longitude": -77.1428, "type": "Container", "locode": "PECLL"},
            {"name": "Port of Valparaiso", "country": "Chile", "latitude": -33.0472, "longitude": -71.6127, "type": "Container", "locode": "CLVAP"},
            {"name": "Port of Buenos Aires", "country": "Argentina", "latitude": -34.6118, "longitude": -58.3960, "type": "Container", "locode": "ARBUE"},
            {"name": "Port of Montevideo", "country": "Uruguay", "latitude": -34.9011, "longitude": -56.1645, "type": "Container", "locode": "UYMVD"},
            {"name": "Port of Cartagena", "country": "Colombia", "latitude": 10.3932, "longitude": -75.4832, "type": "Container", "locode": "COCTG"},
            {"name": "Port of Guayaquil", "country": "Ecuador", "latitude": -2.1894, "longitude": -79.8890, "type": "Container", "locode": "ECGYE"},
            
            # Oceania - Australia
            {"name": "Port of Melbourne", "country": "Australia", "latitude": -37.8136, "longitude": 144.9631, "type": "Container", "locode": "AUMEL"},
            {"name": "Port of Sydney", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093, "type": "Container", "locode": "AUSYD"},
            {"name": "Port of Brisbane", "country": "Australia", "latitude": -27.4705, "longitude": 153.0260, "type": "Container", "locode": "AUBNE"},
            {"name": "Port of Fremantle", "country": "Australia", "latitude": -32.0569, "longitude": 115.7439, "type": "Container", "locode": "AUPER"},
            {"name": "Port of Adelaide", "country": "Australia", "latitude": -34.9285, "longitude": 138.6007, "type": "Container", "locode": "AUADL"},
            
            # Oceania - New Zealand
            {"name": "Port of Auckland", "country": "New Zealand", "latitude": -36.8485, "longitude": 174.7633, "type": "Container", "locode": "NZAKL"},
            {"name": "Port of Tauranga", "country": "New Zealand", "latitude": -37.6878, "longitude": 176.1651, "type": "Container", "locode": "NZTRG"},
            
            # Caribbean and Central America
            {"name": "Port of Kingston", "country": "Jamaica", "latitude": 17.9714, "longitude": -76.7931, "type": "Container/Transshipment", "locode": "JMKIN"},
            {"name": "Port of Freeport", "country": "Bahamas", "latitude": 26.5328, "longitude": -78.6957, "type": "Container/Transshipment", "locode": "BSFPO"},
            {"name": "Port of Colon", "country": "Panama", "latitude": 9.3547, "longitude": -79.9003, "type": "Container/Transshipment", "locode": "PACRI"},
            {"name": "Port of Balboa", "country": "Panama", "latitude": 8.9581, "longitude": -79.5656, "type": "Container", "locode": "PABAL"},
            {"name": "Port of Puerto Cortes", "country": "Honduras", "latitude": 15.8333, "longitude": -87.9167, "type": "Container", "locode": "HNPCE"},
            {"name": "Port of Santo Tomas", "country": "Guatemala", "latitude": 15.6833, "longitude": -88.6167, "type": "Container", "locode": "GTSTO"},
            
            # Pacific Islands
            {"name": "Port of Honolulu", "country": "USA", "latitude": 21.3099, "longitude": -157.8581, "type": "Container/Cruise", "locode": "USHNL"},
            {"name": "Port of Suva", "country": "Fiji", "latitude": -18.1248, "longitude": 178.4501, "type": "Container", "locode": "FJSUV"},
            
            # Arctic Ports
            {"name": "Port of Murmansk", "country": "Russia", "latitude": 68.9585, "longitude": 33.0827, "type": "Container/Bulk", "locode": "RUMMK"},
            {"name": "Port of Arkhangelsk", "country": "Russia", "latitude": 64.5401, "longitude": 40.5433, "type": "Bulk/Timber", "locode": "RUARH"},
            
            # Additional Strategic Ports
            {"name": "Port of Istanbul", "country": "Turkey", "latitude": 41.0082, "longitude": 28.9784, "type": "Container", "locode": "TRIST"},
            {"name": "Port of Piraeus", "country": "Greece", "latitude": 37.9364, "longitude": 23.6503, "type": "Container", "locode": "GRPIR"},
            {"name": "Port of Constanta", "country": "Romania", "latitude": 44.1598, "longitude": 28.6348, "type": "Container", "locode": "ROCND"},
            {"name": "Port of Gdansk", "country": "Poland", "latitude": 54.3520, "longitude": 18.6466, "type": "Container", "locode": "PLGDN"},
            {"name": "Port of Riga", "country": "Latvia", "latitude": 56.9496, "longitude": 24.1052, "type": "Container", "locode": "LVRIX"},
            {"name": "Port of St. Petersburg", "country": "Russia", "latitude": 59.9311, "longitude": 30.3609, "type": "Container", "locode": "RULED"},
            {"name": "Port of Vladivostok", "country": "Russia", "latitude": 43.1056, "longitude": 131.8735, "type": "Container", "locode": "RUVVO"},
            {"name": "Port of Novorossiysk", "country": "Russia", "latitude": 44.7209, "longitude": 37.7854, "type": "Bulk/Oil", "locode": "RUNVS"},
        ]
    
    def _fetch_additional_ports(self) -> List[Dict]:
        """Fetch additional ports from various free APIs"""
        additional_ports = []
        
        try:
            # Try to fetch from a comprehensive ports dataset
            # This is a placeholder for actual API calls
            # You might want to integrate with services like:
            # - OpenStreetMap Overpass API for port data
            # - World Port Index
            # - Maritime databases
            
            logger.info("Fetching additional ports from external sources...")
            # For now, we'll add some more ports manually
            
            # European smaller ports
            additional_ports.extend([
                {"name": "Port of Bilbao", "country": "Spain", "latitude": 43.3614, "longitude": -2.9253, "type": "Container", "locode": "ESBIO"},
                {"name": "Port of Vigo", "country": "Spain", "latitude": 42.2406, "longitude": -8.7207, "type": "Container/Fishing", "locode": "ESVGO"},
                {"name": "Port of Santander", "country": "Spain", "latitude": 43.4623, "longitude": -3.8099, "type": "RoRo/Ferry", "locode": "ESSDR"},
                {"name": "Port of Lisbon", "country": "Portugal", "latitude": 38.7223, "longitude": -9.1393, "type": "Container/Cruise", "locode": "PTLIS"},
                {"name": "Port of Leixoes", "country": "Portugal", "latitude": 41.1844, "longitude": -8.7007, "type": "Container", "locode": "PTLEX"},
                {"name": "Port of Trieste", "country": "Italy", "latitude": 45.6495, "longitude": 13.7768, "type": "Container", "locode": "ITTRS"},
                {"name": "Port of Venice", "country": "Italy", "latitude": 45.4408, "longitude": 12.3155, "type": "Container/Cruise", "locode": "ITVCE"},
                {"name": "Port of Livorno", "country": "Italy", "latitude": 43.5443, "longitude": 10.3261, "type": "Container/Ferry", "locode": "ITLIV"},
                {"name": "Port of Civitavecchia", "country": "Italy", "latitude": 42.0942, "longitude": 11.7969, "type": "Ferry/Cruise", "locode": "ITCVV"},
                {"name": "Port of Gioia Tauro", "country": "Italy", "latitude": 38.4244, "longitude": 15.8986, "type": "Container/Transshipment", "locode": "ITGIT"},
                
                # Asian smaller ports
                {"name": "Port of Kaohsiung", "country": "Taiwan", "latitude": 22.6273, "longitude": 120.3014, "type": "Container", "locode": "TWKHH"},
                {"name": "Port of Keelung", "country": "Taiwan", "latitude": 25.1276, "longitude": 121.7391, "type": "Container", "locode": "TWKEL"},
                {"name": "Port of Colombo", "country": "Sri Lanka", "latitude": 6.9271, "longitude": 79.8612, "type": "Container/Transshipment", "locode": "LKCMB"},
                {"name": "Port of Chittagong", "country": "Bangladesh", "latitude": 22.3569, "longitude": 91.7832, "type": "Container", "locode": "BDCGP"},
                {"name": "Port of Karachi", "country": "Pakistan", "latitude": 24.8607, "longitude": 67.0011, "type": "Container", "locode": "PKKHI"},
                {"name": "Port of Gwadar", "country": "Pakistan", "latitude": 25.1216, "longitude": 62.3254, "type": "Container", "locode": "PKGWD"},
                
                # Middle East smaller ports
                {"name": "Port of Bandar Abbas", "country": "Iran", "latitude": 27.1865, "longitude": 56.2808, "type": "Container", "locode": "IRBND"},
                {"name": "Port of Bushehr", "country": "Iran", "latitude": 28.9684, "longitude": 50.8385, "type": "Container", "locode": "IRBUZ"},
                {"name": "Port of Aqaba", "country": "Jordan", "latitude": 29.5321, "longitude": 35.0061, "type": "Container", "locode": "JOAQJ"},
                {"name": "Port of Beirut", "country": "Lebanon", "latitude": 33.9018, "longitude": 35.5149, "type": "Container", "locode": "LBBEY"},
                {"name": "Port of Latakia", "country": "Syria", "latitude": 35.5211, "longitude": 35.7981, "type": "Container", "locode": "SYLTK"},
                
                # African smaller ports
                {"name": "Port of Walvis Bay", "country": "Namibia", "latitude": -22.9576, "longitude": 14.5052, "type": "Container", "locode": "NAWVB"},
                {"name": "Port of Maputo", "country": "Mozambique", "latitude": -25.9692, "longitude": 32.5732, "type": "Container", "locode": "MZMPM"},
                {"name": "Port of Beira", "country": "Mozambique", "latitude": -19.8437, "longitude": 34.8389, "type": "Container", "locode": "MZBEW"},
                {"name": "Port of Luanda", "country": "Angola", "latitude": -8.8390, "longitude": 13.2894, "type": "Container", "locode": "AOLAD"},
                {"name": "Port of Takoradi", "country": "Ghana", "latitude": 4.8845, "longitude": -1.7554, "type": "Container", "locode": "GHTAK"},
                {"name": "Port of Lome", "country": "Togo", "latitude": 6.1319, "longitude": 1.2228, "type": "Container", "locode": "TGLFW"},
                {"name": "Port of Cotonou", "country": "Benin", "latitude": 6.3703, "longitude": 2.3912, "type": "Container", "locode": "BJCOO"},
                
                # South American smaller ports
                {"name": "Port of San Antonio", "country": "Chile", "latitude": -33.5957, "longitude": -71.6127, "type": "Container", "locode": "CLSAI"},
                {"name": "Port of Iquique", "country": "Chile", "latitude": -20.2208, "longitude": -70.1431, "type": "Container", "locode": "CLIQQ"},
                {"name": "Port of Arica", "country": "Chile", "latitude": -18.4783, "longitude": -70.3126, "type": "Container", "locode": "CLARI"},
                {"name": "Port of Veracruz", "country": "Mexico", "latitude": 19.1738, "longitude": -96.1342, "type": "Container", "locode": "MXVER"},
                {"name": "Port of Manzanillo", "country": "Mexico", "latitude": 19.1143, "longitude": -104.3465, "type": "Container", "locode": "MXZLO"},
                {"name": "Port of Lazaro Cardenas", "country": "Mexico", "latitude": 17.9569, "longitude": -102.2004, "type": "Container", "locode": "MXLZC"},
                {"name": "Port of Altamira", "country": "Mexico", "latitude": 22.3933, "longitude": -97.9303, "type": "Container", "locode": "MXATM"},
                
                # Additional strategic global ports
                {"name": "Port of Sohar", "country": "Oman", "latitude": 24.3473, "longitude": 56.7549, "type": "Container/Industrial", "locode": "OMSOH"},
                {"name": "Port of Muscat", "country": "Oman", "latitude": 23.5859, "longitude": 58.4059, "type": "Container", "locode": "OMMCT"},
                {"name": "Port of Manama", "country": "Bahrain", "latitude": 26.2285, "longitude": 50.5860, "type": "Container", "locode": "BHBAH"},
                {"name": "Port of Haifa", "country": "Israel", "latitude": 32.7940, "longitude": 35.0423, "type": "Container", "locode": "ILHFA"},
                {"name": "Port of Ashdod", "country": "Israel", "latitude": 31.7940, "longitude": 34.6446, "type": "Container", "locode": "ILASD"},
            ])
            
        except Exception as e:
            logger.warning(f"Error fetching additional ports: {e}")
        
        return additional_ports
    
    def _create_fallback_ports_data(self):
        """Create fallback ports data with essential ports"""
        self.ports_data = [
            {"name": "Port of Shanghai", "country": "China", "latitude": 31.2304, "longitude": 121.4737, "type": "Container", "locode": "CNSHA"},
            {"name": "Port of Singapore", "country": "Singapore", "latitude": 1.2966, "longitude": 103.8006, "type": "Container", "locode": "SGSIN"},
            {"name": "Port of Rotterdam", "country": "Netherlands", "latitude": 51.9225, "longitude": 4.4792, "type": "Container", "locode": "NLRTM"},
            {"name": "Port of Los Angeles", "country": "USA", "latitude": 33.7361, "longitude": -118.2645, "type": "Container", "locode": "USLAX"},
            {"name": "Port of Hamburg", "country": "Germany", "latitude": 53.5511, "longitude": 9.9937, "type": "Container", "locode": "DEHAM"},
            {"name": "Port of Dubai", "country": "UAE", "latitude": 25.2854, "longitude": 55.3209, "type": "Container", "locode": "AEDXB"},
            {"name": "Port of Hong Kong", "country": "Hong Kong", "latitude": 22.2783, "longitude": 114.1747, "type": "Container", "locode": "HKHKG"},
        ]
        logger.warning("Using fallback ports data")
    
    def _deduplicate_and_sort(self):
        """Remove duplicates and sort ports"""
        seen = set()
        unique_ports = []
        
        for port in self.ports_data:
            port_key = (port['name'].lower(), port['country'].lower())
            if port_key not in seen:
                seen.add(port_key)
                unique_ports.append(port)
        
        # Sort by country, then by name
        self.ports_data = sorted(unique_ports, key=lambda x: (x['country'], x['name']))
    
    def search_ports(self, query: str, limit: int = 50) -> List[Dict]:
        """Search ports by name, country, or location"""
        if not query:
            return self.ports_data[:limit]
        
        query = query.lower()
        results = []
        
        for port in self.ports_data:
            if (query in port['name'].lower() or 
                query in port['country'].lower() or 
                query in port.get('type', '').lower() or
                query in port.get('locode', '').lower()):
                results.append(port)
        
        return results[:limit]
    
    def get_ports_by_country(self, country: str, limit: int = 100) -> List[Dict]:
        """Get all ports in a specific country"""
        country = country.lower()
        results = []
        
        for port in self.ports_data:
            if country in port['country'].lower():
                results.append(port)
        
        return results[:limit]
    
    def get_ports_by_type(self, port_type: str, limit: int = 100) -> List[Dict]:
        """Get ports by type (Container, Bulk, etc.)"""
        port_type = port_type.lower()
        results = []
        
        for port in self.ports_data:
            if port_type in port.get('type', '').lower():
                results.append(port)
        
        return results[:limit]
    
    def get_nearby_ports(self, latitude: float, longitude: float, radius_km: float = 100, limit: int = 20) -> List[Dict]:
        """Find ports within specified radius"""
        user_location = (latitude, longitude)
        nearby_ports = []
        
        for port in self.ports_data:
            port_location = (port['latitude'], port['longitude'])
            distance = geodesic(user_location, port_location).kilometers
            
            if distance <= radius_km:
                port_with_distance = port.copy()
                port_with_distance['distance_km'] = round(distance, 2)
                nearby_ports.append(port_with_distance)
        
        # Sort by distance
        nearby_ports.sort(key=lambda x: x['distance_km'])
        return nearby_ports[:limit]
    
    def get_port_by_locode(self, locode: str) -> Optional[Dict]:
        """Get port by UN/LOCODE"""
        locode = locode.upper()
        for port in self.ports_data:
            if port.get('locode') == locode:
                return port
        return None
    
    def get_all_ports(self, limit: int = None) -> List[Dict]:
        """Get all ports"""
        if limit:
            return self.ports_data[:limit]
        return self.ports_data
    
    def get_ports_count(self) -> int:
        """Get total number of ports"""
        return len(self.ports_data)
    
    def get_countries_with_ports(self) -> List[str]:
        """Get list of all countries with ports"""
        countries = set()
        for port in self.ports_data:
            countries.add(port['country'])
        return sorted(list(countries))
    
    def get_port_types(self) -> List[str]:
        """Get list of all port types"""
        types = set()
        for port in self.ports_data:
            port_types = port.get('type', '').split('/')
            for port_type in port_types:
                if port_type.strip():
                    types.add(port_type.strip())
        return sorted(list(types))
