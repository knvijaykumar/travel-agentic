// Verified Pan-India Cities covering all 28 States and 8 Union Territories
export interface IndianCityRecord {
  city: string;
  state: string;
  airportCode: string;
  railwayCode: string;
  popular: boolean;
}

export const ALL_INDIAN_CITIES: IndianCityRecord[] = [
  {
    "city": "Bengaluru",
    "state": "Karnataka",
    "airportCode": "BLR",
    "railwayCode": "SBC",
    "popular": true
  },
  {
    "city": "New Delhi",
    "state": "Delhi",
    "airportCode": "DEL",
    "railwayCode": "NDLS",
    "popular": true
  },
  {
    "city": "Mumbai",
    "state": "Maharashtra",
    "airportCode": "BOM",
    "railwayCode": "CSMT",
    "popular": true
  },
  {
    "city": "Goa (Panaji)",
    "state": "Goa",
    "airportCode": "GOI",
    "railwayCode": "MAO",
    "popular": true
  },
  {
    "city": "Jaipur",
    "state": "Rajasthan",
    "airportCode": "JAI",
    "railwayCode": "JP",
    "popular": true
  },
  {
    "city": "Kochi",
    "state": "Kerala",
    "airportCode": "COK",
    "railwayCode": "ERS",
    "popular": true
  },
  {
    "city": "Kolkata",
    "state": "West Bengal",
    "airportCode": "CCU",
    "railwayCode": "HWH",
    "popular": true
  },
  {
    "city": "Chennai",
    "state": "Tamil Nadu",
    "airportCode": "MAA",
    "railwayCode": "MAS",
    "popular": true
  },
  {
    "city": "Hyderabad",
    "state": "Telangana",
    "airportCode": "HYD",
    "railwayCode": "SC",
    "popular": true
  },
  {
    "city": "Varanasi",
    "state": "Uttar Pradesh",
    "airportCode": "VNS",
    "railwayCode": "BSB",
    "popular": true
  },
  {
    "city": "Srinagar",
    "state": "Jammu and Kashmir",
    "airportCode": "SXR",
    "railwayCode": "JAT",
    "popular": true
  },
  {
    "city": "Leh",
    "state": "Ladakh",
    "airportCode": "IXL",
    "railwayCode": "JAT",
    "popular": true
  },
  {
    "city": "Shimla",
    "state": "Himachal Pradesh",
    "airportCode": "SLV",
    "railwayCode": "SML",
    "popular": true
  },
  {
    "city": "Manali",
    "state": "Himachal Pradesh",
    "airportCode": "KUU",
    "railwayCode": "CDG",
    "popular": true
  },
  {
    "city": "Amritsar",
    "state": "Punjab",
    "airportCode": "ATQ",
    "railwayCode": "ASR",
    "popular": true
  },
  {
    "city": "Chandigarh",
    "state": "Chandigarh",
    "airportCode": "IXC",
    "railwayCode": "CDG",
    "popular": true
  },
  {
    "city": "Port Blair",
    "state": "Andaman and Nicobar Islands",
    "airportCode": "IXZ",
    "railwayCode": "N/A",
    "popular": true
  },
  {
    "city": "Havelock Island",
    "state": "Andaman and Nicobar Islands",
    "airportCode": "IXZ",
    "railwayCode": "N/A",
    "popular": false
  },
  {
    "city": "Visakhapatnam",
    "state": "Andhra Pradesh",
    "airportCode": "VTZ",
    "railwayCode": "VSKP",
    "popular": false
  },
  {
    "city": "Tirupati",
    "state": "Andhra Pradesh",
    "airportCode": "TIR",
    "railwayCode": "TPTY",
    "popular": false
  },
  {
    "city": "Vijayawada",
    "state": "Andhra Pradesh",
    "airportCode": "VGA",
    "railwayCode": "BZA",
    "popular": false
  },
  {
    "city": "Itanagar",
    "state": "Arunachal Pradesh",
    "airportCode": "HGI",
    "railwayCode": "HMY",
    "popular": false
  },
  {
    "city": "Tawang",
    "state": "Arunachal Pradesh",
    "airportCode": "TEZ",
    "railwayCode": "RPAN",
    "popular": false
  },
  {
    "city": "Guwahati",
    "state": "Assam",
    "airportCode": "GAU",
    "railwayCode": "GHY",
    "popular": false
  },
  {
    "city": "Kaziranga (Jorhat)",
    "state": "Assam",
    "airportCode": "JRH",
    "railwayCode": "FKG",
    "popular": false
  },
  {
    "city": "Patna",
    "state": "Bihar",
    "airportCode": "PAT",
    "railwayCode": "PNBE",
    "popular": false
  },
  {
    "city": "Gaya (Bodh Gaya)",
    "state": "Bihar",
    "airportCode": "GAY",
    "railwayCode": "GAYA",
    "popular": false
  },
  {
    "city": "Raipur",
    "state": "Chhattisgarh",
    "airportCode": "RPR",
    "railwayCode": "R",
    "popular": false
  },
  {
    "city": "Jagdalpur",
    "state": "Chhattisgarh",
    "airportCode": "JGB",
    "railwayCode": "JDB",
    "popular": false
  },
  {
    "city": "Daman",
    "state": "Dadra & Nagar Haveli and Daman & Diu",
    "airportCode": "NMB",
    "railwayCode": "VAPI",
    "popular": false
  },
  {
    "city": "Diu",
    "state": "Dadra & Nagar Haveli and Daman & Diu",
    "airportCode": "DIU",
    "railwayCode": "VRL",
    "popular": false
  },
  {
    "city": "Ahmedabad",
    "state": "Gujarat",
    "airportCode": "AMD",
    "railwayCode": "ADI",
    "popular": false
  },
  {
    "city": "Surat",
    "state": "Gujarat",
    "airportCode": "STV",
    "railwayCode": "ST",
    "popular": false
  },
  {
    "city": "Kutch (Bhuj)",
    "state": "Gujarat",
    "airportCode": "BHJ",
    "railwayCode": "BHUJ",
    "popular": false
  },
  {
    "city": "Vadodara",
    "state": "Gujarat",
    "airportCode": "BDQ",
    "railwayCode": "BRC",
    "popular": false
  },
  {
    "city": "Gurugram",
    "state": "Haryana",
    "airportCode": "DEL",
    "railwayCode": "GGN",
    "popular": false
  },
  {
    "city": "Faridabad",
    "state": "Haryana",
    "airportCode": "DEL",
    "railwayCode": "FDB",
    "popular": false
  },
  {
    "city": "Dharamshala",
    "state": "Himachal Pradesh",
    "airportCode": "DHM",
    "railwayCode": "PTK",
    "popular": false
  },
  {
    "city": "Kullu",
    "state": "Himachal Pradesh",
    "airportCode": "KUU",
    "railwayCode": "CDG",
    "popular": false
  },
  {
    "city": "Gulmarg",
    "state": "Jammu and Kashmir",
    "airportCode": "SXR",
    "railwayCode": "JAT",
    "popular": false
  },
  {
    "city": "Jammu",
    "state": "Jammu and Kashmir",
    "airportCode": "IXJ",
    "railwayCode": "JAT",
    "popular": false
  },
  {
    "city": "Ranchi",
    "state": "Jharkhand",
    "airportCode": "IXR",
    "railwayCode": "RNC",
    "popular": false
  },
  {
    "city": "Jamshedpur",
    "state": "Jharkhand",
    "airportCode": "IXR",
    "railwayCode": "TATA",
    "popular": false
  },
  {
    "city": "Mysuru",
    "state": "Karnataka",
    "airportCode": "MYQ",
    "railwayCode": "MYS",
    "popular": false
  },
  {
    "city": "Hampi (Hospet)",
    "state": "Karnataka",
    "airportCode": "VDY",
    "railwayCode": "HPT",
    "popular": false
  },
  {
    "city": "Mangaluru",
    "state": "Karnataka",
    "airportCode": "IXE",
    "railwayCode": "MAQ",
    "popular": false
  },
  {
    "city": "Coorg (Madikeri)",
    "state": "Karnataka",
    "airportCode": "MYQ",
    "railwayCode": "MYS",
    "popular": false
  },
  {
    "city": "Munnar",
    "state": "Kerala",
    "airportCode": "COK",
    "railwayCode": "AWY",
    "popular": false
  },
  {
    "city": "Alleppey (Alappuzha)",
    "state": "Kerala",
    "airportCode": "COK",
    "railwayCode": "ALLP",
    "popular": false
  },
  {
    "city": "Thiruvananthapuram",
    "state": "Kerala",
    "airportCode": "TRV",
    "railwayCode": "TVC",
    "popular": false
  },
  {
    "city": "Kozhikode",
    "state": "Kerala",
    "airportCode": "CCJ",
    "railwayCode": "CLT",
    "popular": false
  },
  {
    "city": "Agatti Island",
    "state": "Lakshadweep",
    "airportCode": "AGX",
    "railwayCode": "N/A",
    "popular": false
  },
  {
    "city": "Kavaratti",
    "state": "Lakshadweep",
    "airportCode": "AGX",
    "railwayCode": "N/A",
    "popular": false
  },
  {
    "city": "Bhopal",
    "state": "Madhya Pradesh",
    "airportCode": "BHO",
    "railwayCode": "BPL",
    "popular": false
  },
  {
    "city": "Indore",
    "state": "Madhya Pradesh",
    "airportCode": "IDR",
    "railwayCode": "INDB",
    "popular": false
  },
  {
    "city": "Gwalior",
    "state": "Madhya Pradesh",
    "airportCode": "GWL",
    "railwayCode": "GWL",
    "popular": false
  },
  {
    "city": "Khajuraho",
    "state": "Madhya Pradesh",
    "airportCode": "HJR",
    "railwayCode": "KURJ",
    "popular": false
  },
  {
    "city": "Pune",
    "state": "Maharashtra",
    "airportCode": "PNQ",
    "railwayCode": "PUNE",
    "popular": false
  },
  {
    "city": "Nagpur",
    "state": "Maharashtra",
    "airportCode": "NAG",
    "railwayCode": "NGP",
    "popular": false
  },
  {
    "city": "Aurangabad (Chhatrapati Sambhajinagar)",
    "state": "Maharashtra",
    "airportCode": "IXU",
    "railwayCode": "AWB",
    "popular": false
  },
  {
    "city": "Mahabaleshwar",
    "state": "Maharashtra",
    "airportCode": "PNQ",
    "railwayCode": "PUNE",
    "popular": false
  },
  {
    "city": "Imphal",
    "state": "Manipur",
    "airportCode": "IMF",
    "railwayCode": "DMV",
    "popular": false
  },
  {
    "city": "Shillong",
    "state": "Meghalaya",
    "airportCode": "SHL",
    "railwayCode": "GHY",
    "popular": false
  },
  {
    "city": "Cherrapunji (Sohra)",
    "state": "Meghalaya",
    "airportCode": "SHL",
    "railwayCode": "GHY",
    "popular": false
  },
  {
    "city": "Aizawl",
    "state": "Mizoram",
    "airportCode": "AJL",
    "railwayCode": "SCL",
    "popular": false
  },
  {
    "city": "Kohima",
    "state": "Nagaland",
    "airportCode": "DMU",
    "railwayCode": "DMV",
    "popular": false
  },
  {
    "city": "Dimapur",
    "state": "Nagaland",
    "airportCode": "DMU",
    "railwayCode": "DMV",
    "popular": false
  },
  {
    "city": "Bhubaneswar",
    "state": "Odisha",
    "airportCode": "BBI",
    "railwayCode": "BBS",
    "popular": false
  },
  {
    "city": "Puri",
    "state": "Odisha",
    "airportCode": "BBI",
    "railwayCode": "PURI",
    "popular": false
  },
  {
    "city": "Puducherry (Pondicherry)",
    "state": "Puducherry",
    "airportCode": "PNY",
    "railwayCode": "PDY",
    "popular": false
  },
  {
    "city": "Ludhiana",
    "state": "Punjab",
    "airportCode": "LUH",
    "railwayCode": "LDH",
    "popular": false
  },
  {
    "city": "Udaipur",
    "state": "Rajasthan",
    "airportCode": "UDR",
    "railwayCode": "UDZ",
    "popular": false
  },
  {
    "city": "Jodhpur",
    "state": "Rajasthan",
    "airportCode": "JDH",
    "railwayCode": "JU",
    "popular": false
  },
  {
    "city": "Jaisalmer",
    "state": "Rajasthan",
    "airportCode": "JSA",
    "railwayCode": "JSM",
    "popular": false
  },
  {
    "city": "Gangtok",
    "state": "Sikkim",
    "airportCode": "PYG",
    "railwayCode": "NJP",
    "popular": false
  },
  {
    "city": "Madurai",
    "state": "Tamil Nadu",
    "airportCode": "IXM",
    "railwayCode": "MDU",
    "popular": false
  },
  {
    "city": "Coimbatore",
    "state": "Tamil Nadu",
    "airportCode": "CJB",
    "railwayCode": "CBE",
    "popular": false
  },
  {
    "city": "Ooty",
    "state": "Tamil Nadu",
    "airportCode": "CJB",
    "railwayCode": "UAM",
    "popular": false
  },
  {
    "city": "Warangal",
    "state": "Telangana",
    "airportCode": "HYD",
    "railwayCode": "WL",
    "popular": false
  },
  {
    "city": "Agartala",
    "state": "Tripura",
    "airportCode": "IXA",
    "railwayCode": "AGTL",
    "popular": false
  },
  {
    "city": "Agra",
    "state": "Uttar Pradesh",
    "airportCode": "AGR",
    "railwayCode": "AGC",
    "popular": false
  },
  {
    "city": "Lucknow",
    "state": "Uttar Pradesh",
    "airportCode": "LKO",
    "railwayCode": "LKO",
    "popular": false
  },
  {
    "city": "Ayodhya",
    "state": "Uttar Pradesh",
    "airportCode": "AYJ",
    "railwayCode": "AY",
    "popular": false
  },
  {
    "city": "Prayagraj",
    "state": "Uttar Pradesh",
    "airportCode": "IXD",
    "railwayCode": "PRYJ",
    "popular": false
  },
  {
    "city": "Dehradun",
    "state": "Uttarakhand",
    "airportCode": "DED",
    "railwayCode": "DDN",
    "popular": false
  },
  {
    "city": "Rishikesh",
    "state": "Uttarakhand",
    "airportCode": "DED",
    "railwayCode": "YNRK",
    "popular": false
  },
  {
    "city": "Mussoorie",
    "state": "Uttarakhand",
    "airportCode": "DED",
    "railwayCode": "DDN",
    "popular": false
  },
  {
    "city": "Nainital",
    "state": "Uttarakhand",
    "airportCode": "PGH",
    "railwayCode": "KGM",
    "popular": false
  },
  {
    "city": "Darjeeling",
    "state": "West Bengal",
    "airportCode": "IXB",
    "railwayCode": "DJ",
    "popular": false
  },
  {
    "city": "Siliguri",
    "state": "West Bengal",
    "airportCode": "IXB",
    "railwayCode": "NJP",
    "popular": false
  }
];

export function searchIndianCities(query: string): IndianCityRecord[] {
  const clean = (query || '').trim().toLowerCase();
  if (!clean) {
    // Return top popular suggestions when input is empty
    return ALL_INDIAN_CITIES.filter(c => c.popular);
  }

  return ALL_INDIAN_CITIES.filter(c => 
    c.city.toLowerCase().includes(clean) ||
    c.state.toLowerCase().includes(clean) ||
    c.airportCode.toLowerCase().includes(clean) ||
    c.railwayCode.toLowerCase().includes(clean)
  );
}
