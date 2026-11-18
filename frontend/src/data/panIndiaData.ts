import { Attraction } from '../types/travel.ts';

export interface StateDestination {
  id: string;
  name: string;
  type: 'State' | 'Union Territory';
  capital: string;
  popularAirports: { code: string; name: string; city: string }[];
  overview: string;
  bestSeason: string;
  heroImage: string;
  culturalTags: string[];
  popularActivities: string[];
  attractions: Attraction[];
}

export const PAN_INDIA_DESTINATIONS: StateDestination[] = [
  // 1. Andaman and Nicobar Islands (UT)
  {
    id: 'andaman-nicobar',
    name: 'Andaman and Nicobar Islands',
    type: 'Union Territory',
    capital: 'Port Blair',
    popularAirports: [{ code: 'IXZ', name: 'Veer Savarkar International Airport', city: 'Port Blair' }],
    overview: 'Tropical paradise of turquoise waters, pristine coral reefs, mangrove creeks, and poignant colonial history.',
    bestSeason: 'October to May',
    heroImage: 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Islands', 'Beaches', 'Marine Life', 'Colonial History'],
    popularActivities: ['Scuba diving at Havelock', 'Light & Sound show at Cellular Jail', 'Sea walk at Elephant Beach'],
    attractions: [
      {
        id: 'an-1',
        name: 'Cellular Jail (Kala Pani)',
        state: 'Andaman and Nicobar Islands',
        city: 'Port Blair',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1626014303757-646654261899?auto=format&fit=crop&w=800&q=80',
        description: 'Historic colonial prison that stood as a symbol of India’s freedom struggle, featuring a moving evening sound and light presentation.',
        location: 'Atlanta Point, Port Blair',
        openingHours: '09:00 AM - 05:00 PM (Closed Mondays)',
        entryFee: 30,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Colonial architecture', 'Freedom fighter memorials', 'Sound & Light show']
      },
      {
        id: 'an-2',
        name: 'Radhanagar Beach',
        state: 'Andaman and Nicobar Islands',
        city: 'Havelock Island (Swaraj Dweep)',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80',
        description: 'Renowned as one of Asia’s best beaches, offering powdery white sand, lush rainforest backdrop, and spectacular sunsets.',
        location: 'Havelock Island',
        openingHours: '06:00 AM - 05:30 PM',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Golden hour photography', 'Gentle turquoise surf', 'Lush timberline']
      },
      {
        id: 'an-3',
        name: 'Elephant Beach Coral Reef',
        state: 'Andaman and Nicobar Islands',
        city: 'Havelock Island',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1544551763-77ef2d0cf967?auto=format&fit=crop&w=800&q=80',
        description: 'A vibrant shallow reef hotspot ideal for beginner snorkelling, guided sea walks, jet skiing, and glass-bottom boat tours.',
        location: 'Havelock Island North Coast',
        openingHours: '08:00 AM - 03:00 PM',
        entryFee: 100,
        estimatedDuration: '3 hours',
        rating: 4.7,
        highlights: ['Living coral gardens', 'Snorkelling', 'Sea walking']
      }
    ]
  },

  // 2. Andhra Pradesh
  {
    id: 'andhra-pradesh',
    name: 'Andhra Pradesh',
    type: 'State',
    capital: 'Amaravati',
    popularAirports: [
      { code: 'VTZ', name: 'Visakhapatnam International Airport', city: 'Visakhapatnam' },
      { code: 'TIR', name: 'Tirupati Airport', city: 'Tirupati' }
    ],
    overview: 'Land of sacred shrines, coastal beauty along the Bay of Bengal, prehistoric caves, and rich Kuchipudi heritage.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Sacred Pilgrimage', 'Eastern Ghats', 'Heritage Caves', 'Coastal Cuisine'],
    popularActivities: ['Tirumala temple darshan', 'Visakhapatnam beach drive', 'Coffee plantation stroll in Araku'],
    attractions: [
      {
        id: 'ap-1',
        name: 'Tirumala Venkateswara Temple',
        state: 'Andhra Pradesh',
        city: 'Tirupati',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'The ancient Vaishnavite shrine perched on the Seshachalam Hills, revered as the spiritual epicenter for millions of devotees.',
        location: 'Tirumala, Tirupati Hills',
        openingHours: '04:00 AM - 11:00 PM',
        entryFee: 300,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['Ananda Nilayam gold dome', 'Laddu Prasadam', 'Ancient Dravidian gopuram']
      },
      {
        id: 'ap-2',
        name: 'Borra Caves & Araku Valley',
        state: 'Andhra Pradesh',
        city: 'Visakhapatnam / Araku',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Spectacular limestone karst caves with ancient stalagmites and stalactites in the mist-shrouded Ananthagiri hill range.',
        location: 'Ananthagiri Hills, Alluri Sitharama Raju District',
        openingHours: '10:00 AM - 05:00 PM',
        entryFee: 80,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Speleothem formations', 'Aromas of organic Araku coffee', 'Scenic Vistadome train route']
      },
      {
        id: 'ap-3',
        name: 'Undavalli Rock-Cut Caves',
        state: 'Andhra Pradesh',
        city: 'Vijayawada / Guntur',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Monolithic Indian rock-cut sandstone cave temples dating back to the 4th-5th centuries featuring a giant reclining Vishnu.',
        location: 'Undavalli Village, Amaravati Region',
        openingHours: '09:00 AM - 06:00 PM',
        entryFee: 25,
        estimatedDuration: '1.5 hours',
        rating: 4.5,
        highlights: ['Reclining Anantasayana deity', 'Gupta-style carvings', 'Krishna river vistas']
      }
    ]
  },

  // 3. Arunachal Pradesh
  {
    id: 'arunachal-pradesh',
    name: 'Arunachal Pradesh',
    type: 'State',
    capital: 'Itanagar',
    popularAirports: [{ code: 'HGI', name: 'Donyi Polo Airport', city: 'Itanagar' }],
    overview: 'The Land of Dawn-lit Mountains, boasting snow-crested Himalayan peaks, glacial passes, and centuries-old Mahayana monasteries.',
    bestSeason: 'October to April',
    heroImage: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Himalayan Glaciers', 'Monasteries', 'Tribal Culture', 'Alpine Passes'],
    popularActivities: ['Exploring Tawang Gompa', 'Crossing 13,700 ft Sela Pass', 'Trekking through Ziro pine groves'],
    attractions: [
      {
        id: 'ar-1',
        name: 'Tawang Monastery (Galden Namgey Lhatse)',
        state: 'Arunachal Pradesh',
        city: 'Tawang',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=800&q=80',
        description: 'Founded in 1680-1681, this is India’s largest monastery and second largest in the world, overlooking a scenic alpine valley.',
        location: 'Cona County, Tawang District',
        openingHours: '07:00 AM - 07:00 PM',
        entryFee: 20,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['26 ft gilded Buddha statue', 'Ancient Tibetan scriptures', 'Morning prayer chanting']
      },
      {
        id: 'ar-2',
        name: 'Sela Pass & Sela Lake',
        state: 'Arunachal Pradesh',
        city: 'Tawang Route',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'Breathtaking high-altitude mountain pass at 13,700 ft with prayer flags fluttering beside a frozen turquoise alpine lake.',
        location: 'Border between Tawang and West Kameng',
        openingHours: '24 Hours (Best traversed by daylight)',
        entryFee: 0,
        estimatedDuration: '1.5 hours',
        rating: 4.8,
        highlights: ['High Himalayan snowfields', 'Sela Lake reflection', 'Prayer flag gates']
      },
      {
        id: 'ar-3',
        name: 'Ziro Valley & Apatani Cultural Landscape',
        state: 'Arunachal Pradesh',
        city: 'Ziro',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        description: 'Idyllic UNESCO tentative heritage valley known for its sustainable wet-rice farming, pine hills, and indigenous Apatani villages.',
        location: 'Lower Subansiri District',
        openingHours: 'All day',
        entryFee: 0,
        estimatedDuration: 'Full day',
        rating: 4.7,
        highlights: ['Apatani sustainable bamboo architecture', 'Pine grove trekking', 'Ziro Music Festival venue']
      }
    ]
  },

  // 4. Assam
  {
    id: 'assam',
    name: 'Assam',
    type: 'State',
    capital: 'Dispur / Guwahati',
    popularAirports: [{ code: 'GAU', name: 'Lokpriya Gopinath Bordoloi International Airport', city: 'Guwahati' }],
    overview: 'Gateway to the Northeast, celebrated for its one-horned rhinoceroses, emerald rolling tea estates, and mighty Brahmaputra river.',
    bestSeason: 'November to April',
    heroImage: 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Wildlife Safari', 'Brahmaputra River', 'Assam Tea', 'Shakti Peeth'],
    popularActivities: ['Kaziranga Jeep safari', 'Sunset cruise on Brahmaputra', 'Kamakhya Temple blessing'],
    attractions: [
      {
        id: 'as-1',
        name: 'Kaziranga National Park',
        state: 'Assam',
        city: 'Golaghat / Nagaon',
        category: 'Wildlife',
        image: 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?auto=format&fit=crop&w=800&q=80',
        description: 'World-famous UNESCO World Heritage sanctuary hosting two-thirds of the world’s great one-horned rhinoceros population.',
        location: 'Kanchanjuri, Assam',
        openingHours: '06:00 AM - 04:30 PM (Nov to April)',
        entryFee: 150,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['One-horned rhino sightings', 'Elephant grass meadows', 'Jeep & elephant safaris']
      },
      {
        id: 'as-2',
        name: 'Kamakhya Devi Temple',
        state: 'Assam',
        city: 'Guwahati',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'One of the oldest of the 51 Shakti Peethas, set atop Nilachal Hill overlooking the Brahmaputra with medieval stone carvings.',
        location: 'Nilachal Hills, Guwahati',
        openingHours: '05:30 AM - 06:00 PM',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Ancient Tantric traditions', 'Panoramic Guwahati city vistas', 'Nilachal architecture']
      },
      {
        id: 'as-3',
        name: 'Majuli River Island',
        state: 'Assam',
        city: 'Jorhat / Majuli',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
        description: 'The world’s largest inhabited river island, famous as the heart of Neo-Vaishnavite culture, monastic Satras, and mask-making craft.',
        location: 'Brahmaputra River, Majuli District',
        openingHours: 'All day (Ferry timings 07:00 AM - 03:30 PM)',
        entryFee: 0,
        estimatedDuration: 'Full day',
        rating: 4.7,
        highlights: ['Samaguri Satra bamboo masks', 'Borgeet devotional songs', 'Sunset over sandbanks']
      }
    ]
  },

  // 5. Bihar
  {
    id: 'bihar',
    name: 'Bihar',
    type: 'State',
    capital: 'Patna',
    popularAirports: [{ code: 'PAT', name: 'Jay Prakash Narayan Airport', city: 'Patna' }, { code: 'GAY', name: 'Gaya Airport', city: 'Gaya' }],
    overview: 'Cradle of ancient empires, Buddhism and Jainism, featuring the sacred Bodhi Tree and the ruins of the world’s earliest residential university.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Buddhist Circuit', 'Ancient Universities', 'Heritage', 'Pilgrimage'],
    popularActivities: ['Meditation beneath the Bodhi tree', 'Exploring Nalanda ruins', 'Riding the Rajgir ropeway'],
    attractions: [
      {
        id: 'br-1',
        name: 'Mahabodhi Temple Complex',
        state: 'Bihar',
        city: 'Bodh Gaya',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage landmark marking the sacred location where Siddhartha Gautama attained enlightenment beneath the Bodhi Tree.',
        location: 'Bodh Gaya, Gaya District',
        openingHours: '05:00 AM - 09:00 PM',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Sacred Bodhi Tree', 'Vajrasana diamond throne', '50-meter ancient stone stupa']
      },
      {
        id: 'br-2',
        name: 'Nalanda Mahavihara Ruins',
        state: 'Bihar',
        city: 'Nalanda',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80',
        description: 'The monumental brick ruins of the 5th-century ancient Buddhist academy that housed 10,000 scholars from across Asia.',
        location: 'Bada Gaon, Nalanda',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 40,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Sariputra Stupa stupendous layout', 'Monastery residential cells', 'Sculpture museum']
      },
      {
        id: 'br-3',
        name: 'Rajgir Glass Bridge & Vishwa Shanti Stupa',
        state: 'Bihar',
        city: 'Rajgir',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Skywalk glass bridge suspended over valleys alongside the Japanese peace pagoda atop Ratnagiri hill accessed via chairlift.',
        location: 'Ratnagiri Hills, Rajgir',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 125,
        estimatedDuration: '3 hours',
        rating: 4.6,
        highlights: ['Suspended glass skywalk', 'Chairlift ropeway', 'White marble peace pagoda']
      }
    ]
  },

  // 6. Chandigarh (UT)
  {
    id: 'chandigarh',
    name: 'Chandigarh',
    type: 'Union Territory',
    capital: 'Chandigarh',
    popularAirports: [{ code: 'IXC', name: 'Shaheed Bhagat Singh International Airport', city: 'Chandigarh' }],
    overview: 'The City Beautiful, planned by Le Corbusier, famous for open spaces, urban symmetry, rock gardens, and Sukhna Lake.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1597040663342-45b6af3d91a5?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Modern Architecture', 'Urban Gardens', 'Lakes', 'Clean City'],
    popularActivities: ['Boating on Sukhna Lake', 'Exploring Nek Chand creations', 'Touring UNESCO Capitol Complex'],
    attractions: [
      {
        id: 'ch-1',
        name: 'Nek Chand Rock Garden',
        state: 'Chandigarh',
        city: 'Chandigarh',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1597040663342-45b6af3d91a5?auto=format&fit=crop&w=800&q=80',
        description: 'Spectacular 40-acre visionary sculpture park built entirely out of industrial, domestic waste, ceramic tiles, and discarded bangles.',
        location: 'Sector 1, Chandigarh',
        openingHours: '09:00 AM - 07:00 PM',
        entryFee: 30,
        estimatedDuration: '2.5 hours',
        rating: 4.7,
        highlights: ['Mosaic amphitheatres', 'Recycled ceramic figurines', 'Man-made waterfalls']
      },
      {
        id: 'ch-2',
        name: 'Sukhna Lake Promenade',
        state: 'Chandigarh',
        city: 'Chandigarh',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
        description: 'Serene 3 sq km reservoir at the foothills of Shivalik hills, providing sunset strolls, pedal boating, and migratory bird watching.',
        location: 'Sector 1, Chandigarh',
        openingHours: '05:00 AM - 09:00 PM',
        entryFee: 0,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Sunset promenade walk', 'Pedal boating', 'Shivalik hill views']
      }
    ]
  },

  // 7. Chhattisgarh
  {
    id: 'chhattisgarh',
    name: 'Chhattisgarh',
    type: 'State',
    capital: 'Raipur',
    popularAirports: [{ code: 'RPR', name: 'Swami Vivekananda Airport', city: 'Raipur' }],
    overview: 'Heart of central India’s tribal heartland, dotted with waterfalls, dense Sal forests, bell-metal handicrafts, and historic cave temples.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Niagara of India', 'Tribal Crafts', 'Dense Forests', 'Waterfalls'],
    popularActivities: ['Viewing Chitrakote horseshoe fall', 'Purchasing Dhokra brass art in Jagdalpur', 'Tirathgarh nature walk'],
    attractions: [
      {
        id: 'cg-1',
        name: 'Chitrakote Waterfalls',
        state: 'Chhattisgarh',
        city: 'Bastar / Jagdalpur',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Widest waterfall in India, often celebrated as the ‘Niagara of India’, tumbling 98 ft over a crescent sandstone cliff on Indravati river.',
        location: 'Chitrakoot, Bastar District',
        openingHours: '06:00 AM - 06:30 PM',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.8,
        highlights: ['Horseshoe gorge views', 'Boat ride to spray zone', 'Sunset illumination']
      },
      {
        id: 'cg-2',
        name: 'Tirathgarh Waterfalls & Kanger Valley',
        state: 'Chhattisgarh',
        city: 'Kanger Valley National Park',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=800&q=80',
        description: 'Cascading tiered 300-ft milky waterfall in the middle of pristine bio-diverse Sal forest reserve near deep limestone caves.',
        location: 'Kanger Ghati, Bastar',
        openingHours: '08:00 AM - 04:30 PM',
        entryFee: 25,
        estimatedDuration: '2.5 hours',
        rating: 4.7,
        highlights: ['Stepped white-water cascade', 'Dense flora', 'Kutumsar cave exploration']
      }
    ]
  },

  // 8. Dadra and Nagar Haveli and Daman and Diu (UT)
  {
    id: 'daman-diu-dadra',
    name: 'Dadra & Nagar Haveli and Daman & Diu',
    type: 'Union Territory',
    capital: 'Daman',
    popularAirports: [{ code: 'NMB', name: 'Daman Airport', city: 'Daman' }],
    overview: 'Charming coastal enclaves with 450 years of Portuguese heritage, sea-facing fortresses, palm-fringed beaches, and tranquil lakes.',
    bestSeason: 'October to April',
    heroImage: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Portuguese Forts', 'Sea Breeze', 'Beaches', 'Colonial Churches'],
    popularActivities: ['Strolling Diu Fort ramparts', 'Sunset at Jampore Beach', 'Visiting Bom Jesus Church Daman'],
    attractions: [
      {
        id: 'dd-1',
        name: 'Diu Fort & Lighthouse',
        state: 'Dadra & Nagar Haveli and Daman & Diu',
        city: 'Diu',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'An imposing sea citadel built in 1535 by the Portuguese, offering panoramic Arabian Sea vistas, ancient cannons, and Venetian-style bastions.',
        location: 'Bunder Chowk, Diu Island',
        openingHours: '08:00 AM - 06:00 PM',
        entryFee: 0,
        estimatedDuration: '2 hours',
        rating: 4.7,
        highlights: ['Arabian Sea ocean views', 'Bronze cannons', 'Historic lighthouse']
      },
      {
        id: 'dd-2',
        name: 'Jampore Beach',
        state: 'Dadra & Nagar Haveli and Daman & Diu',
        city: 'Moti Daman',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80',
        description: 'Tranquil dark sand beach shaded by casuarina trees, celebrated for its shallow safe waters, parasailing, and beach shacks.',
        location: 'Near Moti Daman, Daman',
        openingHours: 'Open 24 hours',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.5,
        highlights: ['Parasailing & quad biking', 'Casuarina tree walks', 'Seafood shacks']
      }
    ]
  },

  // 9. Delhi (UT)
  {
    id: 'delhi',
    name: 'Delhi',
    type: 'Union Territory',
    capital: 'New Delhi',
    popularAirports: [{ code: 'DEL', name: 'Indira Gandhi International Airport', city: 'New Delhi' }],
    overview: 'The vibrant historic capital of India, melding Mughal grandeur, Lutyens architecture, bustling street markets, and modern energy.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['UNESCO Monuments', 'Mughal Heritage', 'Street Food', 'Capital Hub'],
    popularActivities: ['Old Delhi heritage food walk', 'Sunset at India Gate', 'Exploring Qutub Minar complex'],
    attractions: [
      {
        id: 'dl-1',
        name: 'Qutub Minar Complex',
        state: 'Delhi',
        city: 'New Delhi',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=800&q=80',
        description: 'A soaring 72.5-meter red sandstone victory tower built in 1192, surrounded by ancient ruins and the rust-resistant 4th-century Iron Pillar.',
        location: 'Mehrauli, New Delhi',
        openingHours: '07:00 AM - 07:00 PM',
        entryFee: 40,
        estimatedDuration: '2 hours',
        rating: 4.8,
        highlights: ['Red sandstone carvings', 'Ancient Iron Pillar of Chandragupta', 'Alai Darwaza']
      },
      {
        id: 'dl-2',
        name: 'Humayun’s Tomb',
        state: 'Delhi',
        city: 'New Delhi',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1608958435020-e8a7109ba809?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage precursor to the Taj Mahal, set within classical Persian Charbagh geometric water garden pathways.',
        location: 'Nizamuddin East, New Delhi',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 40,
        estimatedDuration: '2 hours',
        rating: 4.8,
        highlights: ['Persian Charbagh gardens', 'Red sandstone & white marble dome', 'Sunset photography']
      },
      {
        id: 'dl-3',
        name: 'Red Fort (Lal Qila)',
        state: 'Delhi',
        city: 'Old Delhi',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1598324789736-4861f89564a0?auto=format&fit=crop&w=800&q=80',
        description: 'The monumental 17th-century fortress of Mughal Emperor Shah Jahan, symbolizing Indian sovereignty and independence history.',
        location: 'Netaji Subhash Marg, Chandni Chowk',
        openingHours: '09:30 AM - 04:30 PM (Closed Mondays)',
        entryFee: 50,
        estimatedDuration: '2.5 hours',
        rating: 4.7,
        highlights: ['Diwan-i-Khas marble hall', 'Lahori Gate', 'Sound and light show']
      }
    ]
  },

  // 10. Goa
  {
    id: 'goa',
    name: 'Goa',
    type: 'State',
    capital: 'Panaji',
    popularAirports: [
      { code: 'GOI', name: 'Dabolim International Airport', city: 'Goa' },
      { code: 'GOX', name: 'Manohar International Airport (MOPA)', city: 'Mopa' }
    ],
    overview: 'Sun-drenched coastal state famed for golden sandy shores, Indo-Portuguese architecture, lively beach shacks, and spice plantations.',
    bestSeason: 'November to February',
    heroImage: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Beaches', 'Portuguese Baroque', 'Water Sports', 'Nightlife & Dining'],
    popularActivities: ['Dolphin cruise at Morjim', 'Heritage walk in Fontainhas Panaji', 'Visiting Dudhsagar waterfall'],
    attractions: [
      {
        id: 'ga-1',
        name: 'Basilica of Bom Jesus',
        state: 'Goa',
        city: 'Old Goa',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage Baroque church built in 1605, enshrining the mortal remains of Saint Francis Xavier.',
        location: 'Old Goa Road, Bainguinim',
        openingHours: '09:00 AM - 06:30 PM',
        entryFee: 0,
        estimatedDuration: '1.5 hours',
        rating: 4.8,
        highlights: ['Mausoleum of St. Francis Xavier', 'Baroque gilded altarpiece', 'Laterite exterior']
      },
      {
        id: 'ga-2',
        name: 'Dudhsagar Waterfalls',
        state: 'Goa',
        city: 'Mollem National Park',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=800&q=80',
        description: 'A thunderous 310-meter four-tiered milky cascade on the Mandovi river amidst the dense Western Ghats biodiversity.',
        location: 'Sonaulim, Bhagwan Mahaveer Sanctuary',
        openingHours: '08:30 AM - 04:30 PM',
        entryFee: 100,
        estimatedDuration: '4 hours',
        rating: 4.8,
        highlights: ['Jeep safari through forest rivers', 'Natural plunge pool', 'Railway bridge over cascade']
      },
      {
        id: 'ga-3',
        name: 'Fort Aguada & Lighthouse',
        state: 'Goa',
        city: 'Sinquerim / Candolim',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Well-preserved 17th-century Portuguese fortress and vintage 1864 four-story lighthouse guarding the mouth of Mandovi river.',
        location: 'Aguada Fort Area, Candolim',
        openingHours: '09:30 AM - 06:00 PM',
        entryFee: 25,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Sweeping Arabian Sea panorama', 'Historic freshwater cistern', 'Old jail museum']
      }
    ]
  },

  // 11. Gujarat
  {
    id: 'gujarat',
    name: 'Gujarat',
    type: 'State',
    capital: 'Gandhinagar / Ahmedabad',
    popularAirports: [{ code: 'AMD', name: 'Sardar Vallabhbhai Patel International Airport', city: 'Ahmedabad' }],
    overview: 'Land of the white desert Rann of Kutch, Asiatic lions in Gir, timeless stepwells, and the monumental Statue of Unity.',
    bestSeason: 'November to February',
    heroImage: 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['White Rann', 'Asiatic Lions', 'Stepwells', 'World Tallest Statue'],
    popularActivities: ['Full moon walk on Rann of Kutch', 'Gir safari for lions', 'Visiting Adalaj Stepwell'],
    attractions: [
      {
        id: 'gj-1',
        name: 'Statue of Unity',
        state: 'Gujarat',
        city: 'Kevadia',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'World’s tallest statue at 182 meters, honoring Sardar Vallabhbhai Patel, facing the Narmada dam with high-speed viewing gallery.',
        location: 'Kevadia Colony, Narmada District',
        openingHours: '08:00 AM - 06:00 PM (Closed Mondays)',
        entryFee: 380,
        estimatedDuration: '3.5 hours',
        rating: 4.9,
        highlights: ['Viewing gallery at 153 meters', 'Laser light and sound show', 'Valley of Flowers garden']
      },
      {
        id: 'gj-2',
        name: 'Gir National Park (Sasan Gir)',
        state: 'Gujarat',
        city: 'Junagadh',
        category: 'Wildlife',
        image: 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?auto=format&fit=crop&w=800&q=80',
        description: 'The sole remaining natural wild sanctuary on planet Earth for the magnificent Asiatic lion, surrounded by dry deciduous forest.',
        location: 'Sasan Gir, Gujarat',
        openingHours: '06:00 AM - 05:00 PM (Oct to June)',
        entryFee: 800,
        estimatedDuration: '4 hours',
        rating: 4.8,
        highlights: ['Asiatic Lion safari', 'Leopards and spotted deer', 'Kamleshwar dam reservoir']
      },
      {
        id: 'gj-3',
        name: 'Rann of Kutch (White Desert)',
        state: 'Gujarat',
        city: 'Dhordo, Kutch',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
        description: 'Vast shimmering salt desert marshland coming alive during Rann Utsav with folk music, tent cities, and surreal white horizon.',
        location: 'Dhordo Village, Great Rann of Kutch',
        openingHours: 'Best visited at sunrise & sunset',
        entryFee: 100,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['Full-moon desert walks', 'Kutchi embroidery & crafts', 'Paramotoring & camel rides']
      }
    ]
  },

  // 12. Haryana
  {
    id: 'haryana',
    name: 'Haryana',
    type: 'State',
    capital: 'Chandigarh',
    popularAirports: [{ code: 'DEL', name: 'Indira Gandhi International Airport (Adjacent)', city: 'Delhi / Gurugram' }],
    overview: 'Ancient battleground of Mahabharata, modern corporate tech hub in Gurugram, and serene bird sanctuaries.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Mahabharata Epic', 'Migratory Birds', 'Mughal Terraces', 'Heritage'],
    popularActivities: ['Birdwatching at Sultanpur', 'Brahma Sarovar bath & aarti', 'Yadavindra Gardens evening fountain stroll'],
    attractions: [
      {
        id: 'hr-1',
        name: 'Sultanpur National Park',
        state: 'Haryana',
        city: 'Gurugram',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?auto=format&fit=crop&w=800&q=80',
        description: 'Famous birders paradise sheltering over 250 species of resident and winter migratory birds like Siberian cranes and flamingos.',
        location: 'Gurgaon-Farrukhnagar Road, Sultanpur',
        openingHours: '07:00 AM - 04:30 PM (Closed Tuesdays)',
        entryFee: 40,
        estimatedDuration: '2.5 hours',
        rating: 4.5,
        highlights: ['Watch towers for photography', 'Winter migratory birds', 'Lush wetlands']
      },
      {
        id: 'hr-2',
        name: 'Brahma Sarovar & Kurukshetra',
        state: 'Haryana',
        city: 'Kurukshetra',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Colossal ancient water tank deeply sacred in Hindu mythology, linked to Lord Brahma and the epic Kurukshetra battle.',
        location: 'Thanesar, Kurukshetra',
        openingHours: '05:00 AM - 09:00 PM',
        entryFee: 0,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Evening Maha Aarti', 'Jyotisar Gita birthplace', 'Grand water reservoir']
      }
    ]
  },

  // 13. Himachal Pradesh
  {
    id: 'himachal-pradesh',
    name: 'Himachal Pradesh',
    type: 'State',
    capital: 'Shimla / Dharamshala',
    popularAirports: [
      { code: 'KUU', name: 'Kullu Manali Airport (Bhuntar)', city: 'Kullu' },
      { code: 'DHM', name: 'Kangra Airport', city: 'Dharamshala' }
    ],
    overview: 'The Abode of Snow, boasting snow-capped Himalayan ridges, pine valleys, apple orchards, and Tibetan monastic havens.',
    bestSeason: 'Year-round (Snow in Dec-Feb, Pleasant in Mar-June)',
    heroImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Himalayan Valleys', 'Snow Adventures', 'Tibetan Culture', 'Colonial Hill Stations'],
    popularActivities: ['Solang Valley paragliding', 'Atal Tunnel road trip', 'Mall Road Shimla heritage stroll'],
    attractions: [
      {
        id: 'hp-1',
        name: 'Solang Valley & Rohtang Pass',
        state: 'Himachal Pradesh',
        city: 'Manali',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'Manali’s adventure capital offering paragliding, zorbing, snow skiing, and gateways through the engineering marvel of Atal Tunnel.',
        location: 'Solang, Kullu District',
        openingHours: '08:00 AM - 06:00 PM',
        entryFee: 0,
        estimatedDuration: '4 hours',
        rating: 4.8,
        highlights: ['Snow skiing & quad biking', 'Paragliding over pine valleys', 'Atal Tunnel drive']
      },
      {
        id: 'hp-2',
        name: 'Tsuglagkhang Complex (Dalai Lama Temple)',
        state: 'Himachal Pradesh',
        city: 'McLeod Ganj / Dharamshala',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=800&q=80',
        description: 'The official residence and temple of His Holiness the 14th Dalai Lama, surrounded by cedar forests and prayer wheels.',
        location: 'Temple Road, McLeod Ganj',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 0,
        estimatedDuration: '2 hours',
        rating: 4.9,
        highlights: ['Spinning Tibetan prayer wheels', 'Tibet Museum archives', 'Monks philosophical debate sessions']
      },
      {
        id: 'hp-3',
        name: 'Spiti Valley & Key Monastery',
        state: 'Himachal Pradesh',
        city: 'Spiti',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        description: 'Spectacular high-altitude cold desert valley housing the 1,000-year-old cliffside fort-like Key Gompa perched at 13,668 ft.',
        location: 'Kaza, Lahaul & Spiti District',
        openingHours: '07:00 AM - 06:00 PM',
        entryFee: 0,
        estimatedDuration: 'Full day',
        rating: 4.9,
        highlights: ['Thangka paintings and murals', 'Chander Taal moon lake', 'World highest post office at Hikkim']
      }
    ]
  },

  // 14. Jammu and Kashmir (UT)
  {
    id: 'jammu-kashmir',
    name: 'Jammu and Kashmir',
    type: 'Union Territory',
    capital: 'Srinagar (Summer) / Jammu (Winter)',
    popularAirports: [{ code: 'SXR', name: 'Sheikh ul-Alam International Airport', city: 'Srinagar' }, { code: 'IXJ', name: 'Jammu Airport', city: 'Jammu' }],
    overview: 'Paradise on Earth, celebrated for romantic Shikara rides on Dal Lake, snow meadows of Gulmarg, and Betaab Valley in Pahalgam.',
    bestSeason: 'April to October (Spring/Summer), Dec to Feb (Snow/Skiing)',
    heroImage: 'https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Dal Lake Houseboats', 'Himalayan Skiing', 'Mughal Gardens', 'Saffron & Pashmina'],
    popularActivities: ['Sunset Shikara ride on Dal Lake', 'Riding Gulmarg Gondola Phase 2', 'Pony ride in Betaab Valley'],
    attractions: [
      {
        id: 'jk-1',
        name: 'Dal Lake & Floating Gardens',
        state: 'Jammu and Kashmir',
        city: 'Srinagar',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=800&q=80',
        description: 'Iconic water world of carved cedar houseboats, colorful Shikara water-taxis, and early morning floating vegetable markets.',
        location: 'Boulevard Road, Srinagar',
        openingHours: '05:00 AM - 09:00 PM',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Traditional wood-carved Shikara', 'Early morning floating market', 'Zabarwan mountain reflections']
      },
      {
        id: 'jk-2',
        name: 'Gulmarg Gondola & Apharwat Peak',
        state: 'Jammu and Kashmir',
        city: 'Gulmarg',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'One of the world’s highest operational cable cars taking riders up to 13,780 ft on Apharwat Peak for winter skiing and summer views.',
        location: 'Gulmarg Valley, Baramulla',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 950,
        estimatedDuration: '3.5 hours',
        rating: 4.9,
        highlights: ['Phase 1 & Phase 2 cable car', 'Himalayan snowfields', 'Pine valley slopes']
      },
      {
        id: 'jk-3',
        name: 'Mughal Gardens (Nishat & Shalimar Bagh)',
        state: 'Jammu and Kashmir',
        city: 'Srinagar',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1608958435020-e8a7109ba809?auto=format&fit=crop&w=800&q=80',
        description: 'Terraced imperial Persian-style pleasure gardens commissioned by Emperor Jahangir with fountains, chinar trees, and Dal Lake vistas.',
        location: 'Foreshore Road, Srinagar',
        openingHours: '09:00 AM - 07:00 PM',
        entryFee: 24,
        estimatedDuration: '2 hours',
        rating: 4.7,
        highlights: ['Ancient Chinar canopies', 'Water channels & cascades', 'Panoramic lake viewpoint']
      }
    ]
  },

  // 15. Jharkhand
  {
    id: 'jharkhand',
    name: 'Jharkhand',
    type: 'State',
    capital: 'Ranchi',
    popularAirports: [{ code: 'IXR', name: 'Birsa Munda Airport', city: 'Ranchi' }, { code: 'DGO', name: 'Deoghar Airport', city: 'Deoghar' }],
    overview: 'Land of Forests, famous for cascading waterfalls, sacred Baidyanath Jyotirlinga, Betla National Park, and tribal heritage.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Waterfalls', 'Jyotirlinga', 'Sal Forests', 'Tribal Heartland'],
    popularActivities: ['Visiting Hundru Falls', 'Baidyanath Dham pilgrimage', 'Wildlife tracking in Betla'],
    attractions: [
      {
        id: 'jh-1',
        name: 'Hundru & Jonha Falls',
        state: 'Jharkhand',
        city: 'Ranchi',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=800&q=80',
        description: 'Ranchi’s most spectacular waterfall cascading 320 ft along the Subarnarekha river into rocky pools.',
        location: 'Purulia Road, Ranchi District',
        openingHours: '06:00 AM - 05:00 PM',
        entryFee: 10,
        estimatedDuration: '2.5 hours',
        rating: 4.6,
        highlights: ['320 ft plunge', 'Lush plateau scenery', 'Rocky pools']
      },
      {
        id: 'jh-2',
        name: 'Baba Baidyanath Jyotirlinga Temple',
        state: 'Jharkhand',
        city: 'Deoghar',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'One of the revered twelve Jyotirlingas of Lord Shiva where the sacred Shravani Mela brings millions of Kanwariyas.',
        location: 'Deoghar, Santhal Pargana',
        openingHours: '04:00 AM - 09:00 PM',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Sacred Shiva Jyotirlinga', 'Historic courtyard of 22 temples', 'Shravan month Kanwar yatra']
      }
    ]
  },

  // 16. Karnataka
  {
    id: 'karnataka',
    name: 'Karnataka',
    type: 'State',
    capital: 'Bengaluru',
    popularAirports: [
      { code: 'BLR', name: 'Kempegowda International Airport', city: 'Bengaluru' },
      { code: 'IXE', name: 'Mangaluru International Airport', city: 'Mangaluru' }
    ],
    overview: 'One State, Many Worlds: home to Vijayanagara stone ruins of Hampi, royal Mysore Palace, Coorg coffee hills, and Silicon Valley Bangalore.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Hampi UNESCO Ruins', 'Royal Palaces', 'Coorg Coffee Hills', 'Western Ghats'],
    popularActivities: ['Bouldering & ruin walks in Hampi', 'Mysore Palace illumination view', 'Trekking in Coorg coffee estates'],
    attractions: [
      {
        id: 'ka-1',
        name: 'Hampi Vijayanagara UNESCO Ruins',
        state: 'Karnataka',
        city: 'Hampi / Hospet',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'Vast monumental open-air museum of the 14th-century Vijayanagara Empire with stone chariot, Vittala musical pillars, and Tungabhadra boulders.',
        location: 'Hampi, Vijayanagara District',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 40,
        estimatedDuration: '4.5 hours',
        rating: 4.9,
        highlights: ['Vittala Temple Stone Chariot', 'Virupaksha Temple', 'Sunset over Matanga Hill']
      },
      {
        id: 'ka-2',
        name: 'Mysore Palace (Amba Vilas)',
        state: 'Karnataka',
        city: 'Mysuru',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Spectacular Indo-Saracenic royal seat of the Wadiyar dynasty, illuminated on weekends by over 97,000 incandescent golden bulbs.',
        location: 'Sayyaji Rao Road, Agrahara, Mysuru',
        openingHours: '10:00 AM - 05:30 PM (Illumination Sun 07:00-08:00 PM)',
        entryFee: 100,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Golden Royal Throne', 'Durbar Hall stained glass ceilings', 'Sunday night illumination']
      },
      {
        id: 'ka-3',
        name: 'Abbey Falls & Coorg Coffee Plantations',
        state: 'Karnataka',
        city: 'Madikeri, Kodagu (Coorg)',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Roaring cascade tucked within aromatic coffee estates and spice plantations linked via a scenic hanging suspension footbridge.',
        location: 'Madikeri, Kodagu',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 15,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Aromatic coffee berry trails', 'Suspension bridge waterfall views', 'Kodava authentic cuisine']
      }
    ]
  },

  // 17. Kerala
  {
    id: 'kerala',
    name: 'Kerala',
    type: 'State',
    capital: 'Thiruvananthapuram',
    popularAirports: [
      { code: 'COK', name: 'Cochin International Airport', city: 'Kochi' },
      { code: 'TRV', name: 'Thiruvananthapuram International Airport', city: 'Trivandrum' },
      { code: 'CCJ', name: 'Calicut International Airport', city: 'Kozhikode' }
    ],
    overview: 'God’s Own Country: tranquil palm-lined backwaters, rolling Munnar tea estates, Ayurvedic healing, and Kathakali classical dance.',
    bestSeason: 'September to March',
    heroImage: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Backwaters Houseboats', 'Tea Plantations', 'Ayurveda', 'Kathakali Dance'],
    popularActivities: ['Alleppey houseboat overnight cruise', 'Munnar tea factory trail', 'Watching Kathakali & Kalaripayattu'],
    attractions: [
      {
        id: 'kl-1',
        name: 'Alleppey (Alappuzha) Backwaters',
        state: 'Kerala',
        city: 'Alappuzha',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=800&q=80',
        description: 'Vast labyrinth of palm-fringed canals, lagoons, and Vembanad Lake traversed by traditional thatched Kettuvallam houseboats.',
        location: 'Punnamada Basin, Alappuzha',
        openingHours: 'Houseboats cruise 12:00 PM to 05:30 PM',
        entryFee: 0,
        estimatedDuration: '4 hours / Overnight',
        rating: 4.9,
        highlights: ['Freshly cooked Karimeen fish on deck', 'Paddy fields below sea level', 'Sunset canal cruising']
      },
      {
        id: 'kl-2',
        name: 'Munnar Tea Hills & Eravikulam',
        state: 'Kerala',
        city: 'Munnar',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=800&q=80',
        description: 'Rolling velvet-green tea carpet hills rising towards Anamudi (South India’s highest peak) and home to the endangered Nilgiri Tahr.',
        location: 'Idukki District, Munnar',
        openingHours: '07:30 AM - 04:00 PM',
        entryFee: 200,
        estimatedDuration: '3.5 hours',
        rating: 4.9,
        highlights: ['Nilgiri Tahr mountain goats', 'Tea museum tasting sessions', 'Misty mountain viewpoints']
      },
      {
        id: 'kl-3',
        name: 'Fort Kochi Heritage & Chinese Fishing Nets',
        state: 'Kerala',
        city: 'Kochi',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Cosmopolitan historic port town blending Portuguese churches, Dutch palaces, Jewish synagogues, and cantilevered Chinese fishing nets.',
        location: 'Fort Kochi Beachfront',
        openingHours: 'All day',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.7,
        highlights: ['Cantilevered Chinese fishing nets', 'Jew Town antique shops', 'St. Francis Church']
      }
    ]
  },

  // 18. Ladakh (UT)
  {
    id: 'ladakh',
    name: 'Ladakh',
    type: 'Union Territory',
    capital: 'Leh',
    popularAirports: [{ code: 'IXL', name: 'Kushok Bakula Rimpochee Airport', city: 'Leh' }],
    overview: 'Land of High Passes: dramatic lunar landscapes, turquoise alpine lakes like Pangong Tso, white sand dunes with Bactrian camels, and ancient Gompas.',
    bestSeason: 'May to September',
    heroImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['High Himalayan Deserts', 'Pangong Lake', 'Nubra Dunes', 'Ancient Monasteries'],
    popularActivities: ['Camping at Pangong Lake', 'Riding double-humped camels in Hunder', 'Crossing Khardung La Pass'],
    attractions: [
      {
        id: 'la-1',
        name: 'Pangong Tso Lake',
        state: 'Ladakh',
        city: 'Changthang / Leh',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'World’s highest saltwater lake at 14,270 ft extending 134 km, famous for shifting shades of azure, sapphire, and emerald under clear skies.',
        location: 'Changthang Plateau, Ladakh',
        openingHours: '24 Hours (Inner Line Permit required)',
        entryFee: 0,
        estimatedDuration: 'Full day',
        rating: 4.9,
        highlights: ['Color-changing crystal waters', 'Stargazing at night', 'Striking barren mountain backdrop']
      },
      {
        id: 'la-2',
        name: 'Nubra Valley & Hunder Sand Dunes',
        state: 'Ladakh',
        city: 'Diskit / Hunder',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'Enchanting valley of flowers where cold desert white dunes meet glacial streams, inhabited by rare double-humped Bactrian camels.',
        location: 'Nubra Sub-District',
        openingHours: 'All day',
        entryFee: 0,
        estimatedDuration: 'Full day',
        rating: 4.9,
        highlights: ['Double-humped Bactrian camel safari', '32-meter giant Maitreya Buddha at Diskit', 'Khardung La summit route']
      },
      {
        id: 'la-3',
        name: 'Thiksey Monastery (Mini Potala)',
        state: 'Ladakh',
        city: 'Leh Valley',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=800&q=80',
        description: 'A 12-story whitewashed monastery complex resembling Lhasa’s Potala Palace, housing a 49-ft tall magnificent Maitreya Buddha statue.',
        location: 'Leh-Manali Highway, Thiksey',
        openingHours: '07:00 AM - 07:00 PM',
        entryFee: 30,
        estimatedDuration: '2 hours',
        rating: 4.8,
        highlights: ['Two-story Maitreya Buddha statue', 'Morning prayer hall chanting', 'Indus Valley panoramic view']
      }
    ]
  },

  // 19. Lakshadweep (UT)
  {
    id: 'lakshadweep',
    name: 'Lakshadweep',
    type: 'Union Territory',
    capital: 'Kavaratti',
    popularAirports: [{ code: 'AGX', name: 'Agatti Airport', city: 'Agatti Island' }],
    overview: 'Pristine emerald coral atolls in the Arabian Sea, featuring crystal clear lagoons, white powdery sandbars, and world-class scuba reefs.',
    bestSeason: 'October to May',
    heroImage: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Coral Atolls', 'Lagoon Snorkelling', 'Secluded Beaches', 'Marine Ecosystem'],
    popularActivities: ['Lagoon kayaking at Bangaram', 'Scuba diving among live corals', 'Island hopping by speedboat'],
    attractions: [
      {
        id: 'ld-1',
        name: 'Bangaram Atoll & Sandbank',
        state: 'Lakshadweep',
        city: 'Bangaram Island',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80',
        description: 'Tear-drop shaped uninhabited island encircled by a massive shallow turquoise lagoon, living coral gardens, and shipwreck dives.',
        location: 'Bangaram Island, Lakshadweep',
        openingHours: 'Open all day',
        entryFee: 0,
        estimatedDuration: 'Full day',
        rating: 4.9,
        highlights: ['Phosphorescent night glow waters', 'Shipwreck scuba dive', 'Powder white sandbars']
      },
      {
        id: 'ld-2',
        name: 'Agatti Island Coral Reef',
        state: 'Lakshadweep',
        city: 'Agatti',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1544551763-77ef2d0cf967?auto=format&fit=crop&w=800&q=80',
        description: 'Scenic gateway island with an airstrip flanked by turquoise ocean waters on both sides, offering glass-bottom boat trips and snorkeling.',
        location: 'Agatti Island',
        openingHours: '08:00 AM - 05:30 PM',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.8,
        highlights: ['Runway in the ocean', 'Sea turtle sightings', 'Snorkelling with manta rays']
      }
    ]
  },

  // 20. Madhya Pradesh
  {
    id: 'madhya-pradesh',
    name: 'Madhya Pradesh',
    type: 'State',
    capital: 'Bhopal',
    popularAirports: [{ code: 'IDR', name: 'Devi Ahilyabai Holkar Airport', city: 'Indore' }, { code: 'BHO', name: 'Raja Bhoj Airport', city: 'Bhopal' }],
    overview: 'The Heart of Incredible India: UNESCO world heritage sites of Khajuraho and Sanchi, Kanha tiger reserves, and marble rocks of Bhedaghat.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Tiger Reserves', 'Khajuraho UNESCO Temples', 'Sanchi Buddhist Stupa', 'Royal Forts'],
    popularActivities: ['Kanha tiger safari', 'Exploring erotic carvings of Khajuraho', 'Boat ride through Bhedaghat marble gorge'],
    attractions: [
      {
        id: 'mp-1',
        name: 'Khajuraho Group of Monuments',
        state: 'Madhya Pradesh',
        city: 'Khajuraho',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage complex of Chandela Dynasty temples renowned for their intricate Nagara architecture and sensuous sculptures.',
        location: 'Khajuraho, Chhatarpur District',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 40,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Kandariya Mahadeva Temple', 'Intricate stone relief artwork', 'Evening sound & light show']
      },
      {
        id: 'mp-2',
        name: 'Kanha Tiger Reserve',
        state: 'Madhya Pradesh',
        city: 'Mandla / Balaghat',
        category: 'Wildlife',
        image: 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?auto=format&fit=crop&w=800&q=80',
        description: 'Inspiration behind Rudyard Kipling’s The Jungle Book, famed for its royal Bengal tigers, Barasingha swamp deer, and Sal meadows.',
        location: 'Khatiya Gate, Kanha',
        openingHours: '06:00 AM - 05:00 PM (Oct to June)',
        entryFee: 600,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['Royal Bengal Tiger tracking', 'Hardground Barasingha', 'Sunset at Bamni Dadar']
      },
      {
        id: 'mp-3',
        name: 'Great Stupa at Sanchi',
        state: 'Madhya Pradesh',
        city: 'Sanchi / Vidisha',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80',
        description: 'Oldest stone structure in India commissioned by Emperor Ashoka in the 3rd century BCE, featuring exquisitely carved Torana gateways.',
        location: 'Sanchi, Raisen District',
        openingHours: '06:30 AM - 06:30 PM',
        entryFee: 40,
        estimatedDuration: '2 hours',
        rating: 4.8,
        highlights: ['Ashokan Torana ornamental gateways', 'Buddhist relics', 'Ancient hemispherical dome']
      }
    ]
  },

  // 21. Maharashtra
  {
    id: 'maharashtra',
    name: 'Maharashtra',
    type: 'State',
    capital: 'Mumbai',
    popularAirports: [
      { code: 'BOM', name: 'Chhatrapati Shivaji Maharaj International Airport', city: 'Mumbai' },
      { code: 'PNQ', name: 'Pune International Airport', city: 'Pune' }
    ],
    overview: 'Dynamic gateway of India: financial capital Mumbai, UNESCO cave masterpieces of Ajanta and Ellora, Sahyadri hill forts, and grape vineyards.',
    bestSeason: 'October to March (Monsoons July-Sept for waterfalls)',
    heroImage: 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Ajanta & Ellora', 'Mumbai Skyline', 'Western Ghats Forts', 'Marine Drive'],
    popularActivities: ['Sunset at Marine Drive Mumbai', 'Exploring Ellora Kailasa Temple', 'Wine tasting in Nashik'],
    attractions: [
      {
        id: 'mh-1',
        name: 'Ajanta & Ellora Caves (Kailasa Temple)',
        state: 'Maharashtra',
        city: 'Chhatrapati Sambhajinagar (Aurangabad)',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage rock-cut masterpieces, including Ellora Cave 16 (Kailasa Temple), the largest monolithic rock excavation on Earth.',
        location: 'Ellora & Ajanta, Maharashtra',
        openingHours: '09:00 AM - 05:30 PM (Ajanta closed Mon, Ellora closed Tue)',
        entryFee: 40,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['Monolithic Kailasa rock carving', 'Ancient Buddhist frescoes at Ajanta', '34 rock-hewn sanctuaries']
      },
      {
        id: 'mh-2',
        name: 'Gateway of India & Marine Drive',
        state: 'Maharashtra',
        city: 'Mumbai',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=800&q=80',
        description: 'Monumental 26-meter basalt arch built in 1924 overlooking Mumbai harbour alongside the iconic Taj Mahal Palace Hotel.',
        location: 'Apollo Bunder, Colaba, Mumbai',
        openingHours: 'Open 24 hours',
        entryFee: 0,
        estimatedDuration: '2 hours',
        rating: 4.7,
        highlights: ['Colonial basalt architecture', 'Queen’s Necklace night lights', 'Ferry rides to Elephanta Caves']
      },
      {
        id: 'mh-3',
        name: 'Mahabaleshwar & Panchgani Tableland',
        state: 'Maharashtra',
        city: 'Mahabaleshwar',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Picturesque Sahyadri hill retreat famed for sweet strawberry farms, Arthur’s Seat cliff edge, and Venna Lake boating.',
        location: 'Satara District',
        openingHours: '06:00 AM - 07:00 PM',
        entryFee: 0,
        estimatedDuration: '3.5 hours',
        rating: 4.6,
        highlights: ['Fresh strawberry & cream stalls', 'Arthur’s Seat canyon vistas', 'Venna lake paddle boats']
      }
    ]
  },

  // 22. Manipur
  {
    id: 'manipur',
    name: 'Manipur',
    type: 'State',
    capital: 'Imphal',
    popularAirports: [{ code: 'IMF', name: 'Bir Tikendrajit International Airport', city: 'Imphal' }],
    overview: 'Jewel of India, home to the world’s only floating national park on Loktak Lake, dancing Sangai deer, and ancient martial arts.',
    bestSeason: 'October to April',
    heroImage: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Floating Phumdis', 'Sangai Deer', 'Ima Keithel Market', 'Hills'],
    popularActivities: ['Boating on Loktak Lake', 'Shopping at women-run Ima Keithel', 'Visiting Kangla Fort'],
    attractions: [
      {
        id: 'mn-1',
        name: 'Loktak Lake & Keibul Lamjao',
        state: 'Manipur',
        city: 'Moirang / Bishnupur',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
        description: 'Largest freshwater lake in Northeast India, famous for floating circular biomass islands (Phumdis) and the endangered Sangai brow-antlered deer.',
        location: 'Moirang, Bishnupur District',
        openingHours: '08:00 AM - 05:00 PM',
        entryFee: 50,
        estimatedDuration: '3.5 hours',
        rating: 4.8,
        highlights: ['Unique floating Phumdi ecosystem', 'Endangered Sangai dancing deer', 'Sendra Island panoramic viewpoint']
      },
      {
        id: 'mn-2',
        name: 'Kangla Fort',
        state: 'Manipur',
        city: 'Imphal',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Ancient royal seat of the Meitei rulers on the banks of Imphal river, featuring moats, sacred coronation halls, and shrines.',
        location: 'Kangla, Imphal East',
        openingHours: '09:00 AM - 04:30 PM (Closed Wednesdays)',
        entryFee: 20,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Kangla Sha dragon sculptures', 'Historical citadel moat', 'Govindaji Temple']
      }
    ]
  },

  // 23. Meghalaya
  {
    id: 'meghalaya',
    name: 'Meghalaya',
    type: 'State',
    capital: 'Shillong',
    popularAirports: [{ code: 'SHL', name: 'Shillong Airport (Umroi)', city: 'Shillong' }, { code: 'GAU', name: 'Guwahati Airport (Nearby)', city: 'Guwahati' }],
    overview: 'The Abode of the Clouds: bio-engineered living root bridges, crystal-clear Dawki river, wettest places on Earth (Cherrapunji/Mawsynram).',
    bestSeason: 'September to May',
    heroImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Living Root Bridges', 'Crystal Rivers', 'Waterfalls', 'Scotland of the East'],
    popularActivities: ['Trekking to Double Decker Living Root Bridge', 'Boating on transparent Dawki river', 'Exploring Mawsmai Caves'],
    attractions: [
      {
        id: 'mg-1',
        name: 'Double Decker Living Root Bridge',
        state: 'Meghalaya',
        city: 'Cherrapunji (Sohra)',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Spectacular indigenous engineering wonder created by weaving aerial roots of Ficus elastica trees across rushing jungle streams over decades.',
        location: 'Nongriat Village, Sohra',
        openingHours: 'Sunrise to Sunset',
        entryFee: 50,
        estimatedDuration: '5 hours (requires 3,000 steps trek)',
        rating: 4.9,
        highlights: ['Two-tiered living bio-bridges', 'Natural turquoise swimming lagoons', 'Lush rainforest canopy']
      },
      {
        id: 'mg-2',
        name: 'Dawki Umngot River',
        state: 'Meghalaya',
        city: 'Dawki',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80',
        description: 'Famed for water so crystalline that country wooden boats appear suspended in mid-air over the pebble-strewn riverbed.',
        location: 'West Jaintia Hills, India-Bangladesh Border',
        openingHours: '07:00 AM - 05:00 PM',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Crystal-clear boat rides', 'Suspension bridge vistas', 'Border trade viewpoint']
      },
      {
        id: 'mg-3',
        name: 'Nohkalikai Falls',
        state: 'Meghalaya',
        city: 'Cherrapunji (Sohra)',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=800&q=80',
        description: 'Tallest plunge waterfall in India at 1,115 ft, plunging from red cliffs into a surreal emerald-green water pool.',
        location: 'Near Sohra, East Khasi Hills',
        openingHours: '06:00 AM - 05:00 PM',
        entryFee: 20,
        estimatedDuration: '1.5 hours',
        rating: 4.8,
        highlights: ['Dramatic 1,115 ft single plunge', 'Emerald green plunge pool', 'Misty cloud vortexes']
      }
    ]
  },

  // 24. Mizoram
  {
    id: 'mizoram',
    name: 'Mizoram',
    type: 'State',
    capital: 'Aizawl',
    popularAirports: [{ code: 'AJL', name: 'Lengpui Airport', city: 'Aizawl' }],
    overview: 'Land of the Blue Mountains, covered in bamboo forests, undulating hills, dramatic waterfalls, and gentle Mizo hospitable culture.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Blue Mountains', 'Bamboo Forests', 'Mizo Heritage', 'Serene Hills'],
    popularActivities: ['Trekking Reiek Peak', 'Viewing Vantawng Falls', 'Visiting Solomon’s Temple Aizawl'],
    attractions: [
      {
        id: 'mz-1',
        name: 'Reiek Tlang Peak & Heritage Village',
        state: 'Mizoram',
        city: 'Aizawl',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        description: 'Picturesque mountain peak at 1,548 meters offering 360-degree vistas of surrounding valleys and an authentic traditional Mizo village.',
        location: 'Mamit District, 29 km from Aizawl',
        openingHours: '06:00 AM - 05:00 PM',
        entryFee: 20,
        estimatedDuration: '3 hours',
        rating: 4.7,
        highlights: ['Panoramic valley sunsets', 'Reconstructed tribal chieftain huts', 'Lush forest hiking paths']
      },
      {
        id: 'mz-2',
        name: 'Vantawng Falls',
        state: 'Mizoram',
        city: 'Thenzawl',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=800&q=80',
        description: 'Highest waterfall in Mizoram tumbling 750 ft in two tiers amidst dense virgin bamboo forests.',
        location: 'Serchhip District, Near Thenzawl',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 10,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['750-ft two-tiered cascade', 'Viewing tower observation point', 'Thenzawl handloom weavers']
      }
    ]
  },

  // 25. Nagaland
  {
    id: 'nagaland',
    name: 'Nagaland',
    type: 'State',
    capital: 'Kohima',
    popularAirports: [{ code: 'DMU', name: 'Dimapur Airport', city: 'Dimapur' }],
    overview: 'Land of Festivals, celebrated for the Hornbill Festival at Kisama, pristine Dzukou Valley bamboo valleys, and Khonoma eco-village.',
    bestSeason: 'October to May (Hornbill Festival early Dec)',
    heroImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Hornbill Festival', 'Dzukou Valley', 'Naga Warrior Traditions', 'Eco Villages'],
    popularActivities: ['Trekking in Dzukou Valley', 'Experiencing Hornbill Festival at Kisama', 'Visiting Kohima War Cemetery'],
    attractions: [
      {
        id: 'nl-1',
        name: 'Dzukou Valley',
        state: 'Nagaland',
        city: 'Kohima / Jakhama',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
        description: 'Enchanting high-altitude valley of rolling emerald green dwarf-bamboo dunes and rare seasonal Dzukou lilies.',
        location: 'Border of Nagaland and Manipur',
        openingHours: 'Best hiked starting early morning',
        entryFee: 50,
        estimatedDuration: 'Full day trek',
        rating: 4.9,
        highlights: ['Rare Dzukou lily blooms', 'Serpentine crystal brooks', 'Undulating emerald mounds']
      },
      {
        id: 'nl-2',
        name: 'Kisama Naga Heritage Village',
        state: 'Nagaland',
        city: 'Kohima',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Traditional open-air arena that showcases the architectural Morung dormitories and festive dances of Nagaland’s 16 major tribes.',
        location: '12 km south of Kohima',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 30,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Tribal Morung wood architecture', 'Hornbill Festival ground', 'World War II museum']
      }
    ]
  },

  // 26. Odisha
  {
    id: 'odisha',
    name: 'Odisha',
    type: 'State',
    capital: 'Bhubaneswar',
    popularAirports: [{ code: 'BBI', name: 'Biju Patnaik International Airport', city: 'Bhubaneswar' }],
    overview: 'Land of Lord Jagannath: the 13th-century Konark Sun Temple chariot, Asia’s largest brackish lagoon Chilika Lake, and golden sands of Puri.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Konark Sun Temple', 'Jagannath Puri', 'Chilika Dolphins', 'Kalinga Architecture'],
    popularActivities: ['Dolphin spotting in Chilika Lake', 'Sunset at Konark Sun Temple', 'Puri golden beach stroll'],
    attractions: [
      {
        id: 'od-1',
        name: 'Konark Sun Temple (Black Pagoda)',
        state: 'Odisha',
        city: 'Konark',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage 13th-century monument designed as a monumental 24-wheeled chariot of Surya the Sun God pulled by seven horses.',
        location: 'Konark, Puri District',
        openingHours: '06:00 AM - 08:00 PM',
        entryFee: 40,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Astronomically precise sun dial wheels', 'Exquisite Chlorite stone carvings', 'Evening projection mapping show']
      },
      {
        id: 'od-2',
        name: 'Chilika Lake & Satapada',
        state: 'Odisha',
        city: 'Satapada / Puri',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
        description: 'Asia’s largest brackish lagoon and Ramsar wetland home to endangered Irrawaddy dolphins and thousands of migratory flamingos.',
        location: 'Satapada, Puri District',
        openingHours: '06:00 AM - 05:00 PM',
        entryFee: 0,
        estimatedDuration: '3.5 hours',
        rating: 4.8,
        highlights: ['Irrawaddy dolphin boat spotting', 'Sea mouth confluence point', 'Kalijai Island temple']
      },
      {
        id: 'od-3',
        name: 'Shree Jagannath Temple',
        state: 'Odisha',
        city: 'Puri',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'Sacred Char Dham shrine dating to the 12th century, famed for its massive wooden deities, world’s largest traditional kitchen, and Ratha Yatra.',
        location: 'Grand Road, Puri',
        openingHours: '05:30 AM - 10:00 PM',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.9,
        highlights: ['World largest temple kitchen (Mahaprasad)', 'Neelachakra spire flag change ritual', 'Sacred Aruna Stambha']
      }
    ]
  },

  // 27. Puducherry (UT)
  {
    id: 'puducherry',
    name: 'Puducherry',
    type: 'Union Territory',
    capital: 'Puducherry',
    popularAirports: [{ code: 'PNY', name: 'Puducherry Airport', city: 'Puducherry' }, { code: 'MAA', name: 'Chennai Airport (Nearby)', city: 'Chennai' }],
    overview: 'The French Riviera of the East: pastel colonial villas with bougainvillea, cobblestone streets of White Town, beachfront promenade, and Auroville.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['French Colonial Quarter', 'Auroville Matrimandir', 'Beach Promenade', 'Cafes'],
    popularActivities: ['Cycling through French Quarter', 'Meditation at Matrimandir viewing point', 'Sunset at Promenade beach'],
    attractions: [
      {
        id: 'py-1',
        name: 'Auroville & Matrimandir',
        state: 'Puducherry',
        city: 'Auroville',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=800&q=80',
        description: 'Universal township dedicated to peace, featuring the striking golden geodesic sphere of Matrimandir set in amphitheatre gardens.',
        location: 'Auroville International Township',
        openingHours: '09:00 AM - 04:30 PM (Closed Sunday afternoons)',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.8,
        highlights: ['Golden geodesic sphere', 'Inner concentration chamber', 'Organic sustainable cafes']
      },
      {
        id: 'py-2',
        name: 'French Quarter (White Town) & Promenade Beach',
        state: 'Puducherry',
        city: 'Puducherry',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Charming French colonial streetscapes with mustard-yellow walls, heritage boutique hotels, chic cafes, and a 1.5 km vehicular-free seaside promenade.',
        location: 'Goubert Avenue / White Town',
        openingHours: 'Promenade open all day (No vehicles 6 PM to 7:30 AM)',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.7,
        highlights: ['Mustard yellow French facades', 'Goubert seaside promenade', 'Sri Aurobindo Ashram']
      }
    ]
  },

  // 28. Punjab
  {
    id: 'punjab',
    name: 'Punjab',
    type: 'State',
    capital: 'Chandigarh',
    popularAirports: [{ code: 'ATQ', name: 'Sri Guru Ram Dass Jee International Airport', city: 'Amritsar' }],
    overview: 'Land of Five Rivers: the ethereal Golden Temple, stirring Wagah Border ceremony, rich agricultural fields, and world-famed Punjabi hospitality.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Golden Temple', 'Wagah Border', 'Langar Seva', 'Punjabi Cuisine'],
    popularActivities: ['Night view of Golden Temple', 'Witnessing Wagah retreat ceremony', 'Volunteering in Guru Ram Das Langar'],
    attractions: [
      {
        id: 'pb-1',
        name: 'Sri Harmandir Sahib (The Golden Temple)',
        state: 'Punjab',
        city: 'Amritsar',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=800&q=80',
        description: 'The holiest shrine of Sikhism, coated in pure gold leaf, standing serenely in the center of the sacred Amrit Sarovar tank.',
        location: 'Golden Temple Road, Amritsar',
        openingHours: 'Open 24 hours',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 5.0,
        highlights: ['Golden sanctum gilded with 500 kg gold', 'World’s largest free community kitchen (Langar)', 'Palki Sahib ceremony']
      },
      {
        id: 'pb-2',
        name: 'Wagah Border Beating Retreat Ceremony',
        state: 'Punjab',
        city: 'Attari / Amritsar',
        category: 'Cultural',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Electrifying daily military parade and lowering-of-the-flags ceremony performed by Border Security Force (BSF) and Pakistan Rangers.',
        location: 'Attari-Wagah Border, 30 km from Amritsar',
        openingHours: '04:30 PM - 06:00 PM daily',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['High-stepping synchronized drills', 'Patriotic crowd celebrations', 'Grand stadium atmosphere']
      },
      {
        id: 'pb-3',
        name: 'Jallianwala Bagh Memorial',
        state: 'Punjab',
        city: 'Amritsar',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1598324789736-4861f89564a0?auto=format&fit=crop&w=800&q=80',
        description: 'Historic public garden preserving the tragic bullet-scarred walls, the martyrs’ well, and eternal flame from the 1919 massacre.',
        location: 'Adjacent to Golden Temple, Amritsar',
        openingHours: '06:30 AM - 07:30 PM',
        entryFee: 0,
        estimatedDuration: '1 hour',
        rating: 4.7,
        highlights: ['Bullet marks on heritage brick walls', 'Martyrs’ Well', 'Eternal Flame of remembrance']
      }
    ]
  },

  // 29. Rajasthan
  {
    id: 'rajasthan',
    name: 'Rajasthan',
    type: 'State',
    capital: 'Jaipur',
    popularAirports: [
      { code: 'JAI', name: 'Jaipur International Airport', city: 'Jaipur' },
      { code: 'UDR', name: 'Maharana Pratap Airport', city: 'Udaipur' },
      { code: 'JDH', name: 'Jodhpur Airport', city: 'Jodhpur' }
    ],
    overview: 'The Land of Kings: majestic hill forts of Amber and Mehrangarh, shimmering lakes of Udaipur, sand dunes of Jaisalmer, and royal Rajput heritage.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Royal Forts', 'Palaces & Lakes', 'Thar Desert Dunes', 'Folk Music & Puppetry'],
    popularActivities: ['Amber Fort elephant or jeep ride', 'Sunset boat ride on Lake Pichola', 'Desert safari at Sam dunes'],
    attractions: [
      {
        id: 'rj-1',
        name: 'Amber Palace & Fort',
        state: 'Rajasthan',
        city: 'Jaipur',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80',
        description: 'Imposing UNESCO World Heritage hilltop fort-palace blending Rajput and Mughal architecture, famed for the glittering Sheesh Mahal mirror palace.',
        location: 'Devisinghpura, Amer, Jaipur',
        openingHours: '08:00 AM - 05:30 PM & 06:30 PM - 09:15 PM (Night tourism)',
        entryFee: 100,
        estimatedDuration: '3.5 hours',
        rating: 4.9,
        highlights: ['Sheesh Mahal (Hall of Mirrors)', 'Maota Lake panoramic reflection', 'Evening sound and light show']
      },
      {
        id: 'rj-2',
        name: 'Hawa Mahal (Palace of Winds)',
        state: 'Rajasthan',
        city: 'Jaipur',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80',
        description: 'Five-story pink sandstone crown palace built in 1799 with 953 intricately carved Jharokha honeycomb windows designed for royal women.',
        location: 'Hawa Mahal Rd, Badi Choupad, Jaipur',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 50,
        estimatedDuration: '1.5 hours',
        rating: 4.7,
        highlights: ['953 latticework Jharokhas', 'Pink city skyline vistas', 'Stained glass window reflections']
      },
      {
        id: 'rj-3',
        name: 'City Palace & Lake Pichola',
        state: 'Rajasthan',
        city: 'Udaipur',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Monumental white marble palace complex perched on the banks of Lake Pichola with courtyards, crystal gallery, and sunset boat rides.',
        location: 'Old City, Udaipur',
        openingHours: '09:30 AM - 05:30 PM',
        entryFee: 300,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Sunset boat cruise to Jag Mandir', 'Mor Chowk peacock mosaics', 'Vintage car collection']
      },
      {
        id: 'rj-4',
        name: 'Mehrangarh Fort',
        state: 'Rajasthan',
        city: 'Jodhpur',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Towering 400 ft above the Blue City of Jodhpur, this colossal citadel houses palanquin galleries, artillery bastions, and zip-lining over moats.',
        location: 'Fort Rd, Jodhpur',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 100,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Blue City aerial panorama', 'Royal palanquin & arms museum', 'Flying Fox zip-line adventure']
      }
    ]
  },

  // 30. Sikkim
  {
    id: 'sikkim',
    name: 'Sikkim',
    type: 'State',
    capital: 'Gangtok',
    popularAirports: [{ code: 'PYG', name: 'Pakyong Airport', city: 'Pakyong' }, { code: 'IXB', name: 'Bagdogra Airport (Nearby)', city: 'Bagdogra' }],
    overview: 'India’s first 100% organic state: panoramic views of Mount Kangchenjunga, sacred Tsomgo Lake, Nathu La Indo-China border pass, and flower valleys.',
    bestSeason: 'March to May (Flowers) & Oct to mid-Dec (Clear Peaks)',
    heroImage: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Kangchenjunga Views', 'Glacial Lakes', 'Monasteries', 'Organic State'],
    popularActivities: ['Yak ride at Tsomgo Lake', 'Visiting Nathula Pass border', 'Rumtek monastery chanting'],
    attractions: [
      {
        id: 'sk-1',
        name: 'Tsomgo (Changu) Lake & Nathula Pass',
        state: 'Sikkim',
        city: 'East Sikkim',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'Sacred glacial lake perched at 12,310 ft changing colors with seasons, surrounded by snow peaks and gateway to the historic Silk Route pass.',
        location: 'Jawaharlal Nehru Road, East Sikkim',
        openingHours: '07:30 AM - 03:00 PM (Requires Permit)',
        entryFee: 200,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['Colorfully decorated yaks', 'Snowcapped alpine vistas', 'Ropeway ride over frozen lake']
      },
      {
        id: 'sk-2',
        name: 'Rumtek Dharma Chakra Centre',
        state: 'Sikkim',
        city: 'Gangtok',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=800&q=80',
        description: 'Largest monastery in Sikkim and the seat of the Karma Kagyu lineage, showcasing exquisite thangkas, golden stupa, and Tibetan architecture.',
        location: 'Rumtek, 24 km from Gangtok',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 20,
        estimatedDuration: '2 hours',
        rating: 4.8,
        highlights: ['Golden Stupa containing relics of 16th Karmapa', 'Tibetan monastic debates', 'Panoramic hills view']
      }
    ]
  },

  // 31. Tamil Nadu
  {
    id: 'tamil-nadu',
    name: 'Tamil Nadu',
    type: 'State',
    capital: 'Chennai',
    popularAirports: [
      { code: 'MAA', name: 'Chennai International Airport', city: 'Chennai' },
      { code: 'IXM', name: 'Madurai Airport', city: 'Madurai' },
      { code: 'CJB', name: 'Coimbatore International Airport', city: 'Coimbatore' }
    ],
    overview: 'Land of Temples and Dravidian culture: towering Gopurams of Madurai, monumental UNESCO Chola temples, Ooty hill toy trains, and Marina Beach.',
    bestSeason: 'November to March',
    heroImage: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Dravidian Gopurams', 'UNESCO Living Chola Temples', 'Nilgiri Toy Train', 'Carnatic Music'],
    popularActivities: ['Madurai Meenakshi temple night ceremony', 'Shore temple walk in Mahabalipuram', 'Nilgiri mountain railway steam ride'],
    attractions: [
      {
        id: 'tn-1',
        name: 'Meenakshi Amman Temple',
        state: 'Tamil Nadu',
        city: 'Madurai',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'Magnificent 14-gopuram Dravidian temple complex dedicated to Goddess Meenakshi, adorned with thousands of polychrome mythological statues.',
        location: 'Madurai Main, Madurai',
        openingHours: '05:00 AM - 12:30 PM & 04:00 PM - 10:00 PM',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Hall of Thousand Pillars', 'Night bedtime palanquin procession', 'Golden Lotus sacred tank']
      },
      {
        id: 'tn-2',
        name: 'Brihadeeswara Temple (Big Temple)',
        state: 'Tamil Nadu',
        city: 'Thanjavur',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage Great Living Chola Temple built by Rajaraja Chola I in 1010 CE with an 80-tonne monolithic granite dome apex.',
        location: 'Membalam Rd, Thanjavur',
        openingHours: '06:00 AM - 12:30 PM & 04:00 PM - 08:30 PM',
        entryFee: 0,
        estimatedDuration: '2.5 hours',
        rating: 4.9,
        highlights: ['80-tonne single granite capstone', 'Huge monolithic Nandi bull', 'Chola period fresco murals']
      },
      {
        id: 'tn-3',
        name: 'Mahabalipuram Shore Temple & Pancha Rathas',
        state: 'Tamil Nadu',
        city: 'Mamallapuram',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: '7th-century coastal Pallava rock-cut structural temples and monolithic chariots standing proudly against the Bay of Bengal surf.',
        location: 'Mamallapuram Beach Road',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 40,
        estimatedDuration: '2.5 hours',
        rating: 4.8,
        highlights: ['Shore Temple ocean backdrop', 'Arjuna’s Penance bas-relief', 'Pancha Rathas monolithic chariots']
      }
    ]
  },

  // 32. Telangana
  {
    id: 'telangana',
    name: 'Telangana',
    type: 'State',
    capital: 'Hyderabad',
    popularAirports: [{ code: 'HYD', name: 'Rajiv Gandhi International Airport', city: 'Hyderabad' }],
    overview: 'Land of Nizami splendour and Kakatiya heritage: iconic Charminar, acoustic marvels of Golconda Fort, and UNESCO Ramappa Temple.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Nizami Heritage', 'Charminar & Pearls', 'Biryani Culinary Tour', 'Kakatiya Architecture'],
    popularActivities: ['Climbing Golconda Fort for sunset', 'Savoring authentic Hyderabadi Dum Biryani', 'Boating at Hussain Sagar'],
    attractions: [
      {
        id: 'tg-1',
        name: 'Charminar & Laad Bazaar',
        state: 'Telangana',
        city: 'Hyderabad',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=800&q=80',
        description: 'Monumental 1591 mosque-gateway with four 48.7-meter minarets, surrounded by the bustling perfume, lacquer bangle, and pearl markets.',
        location: 'Char Kaman, Ghansi Bazaar, Hyderabad',
        openingHours: '09:30 AM - 05:30 PM',
        entryFee: 25,
        estimatedDuration: '2 hours',
        rating: 4.7,
        highlights: ['Upper gallery Old City view', 'Laad Bazaar lacquer bangles', 'Irani Chai and Osmania biscuits']
      },
      {
        id: 'tg-2',
        name: 'Golconda Fort & Sound & Light Show',
        state: 'Telangana',
        city: 'Hyderabad',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Impregnable medieval citadel of the Qutb Shahi kings renowned for its ingenious acoustic clapping portico and diamond vault history.',
        location: 'Ibrahim Bagh, Hyderabad',
        openingHours: '09:00 AM - 05:30 PM',
        entryFee: 25,
        estimatedDuration: '3 hours',
        rating: 4.8,
        highlights: ['Acoustic Fateh Darwaza clapping test', 'Baradari hilltop panorama', 'Koh-i-Noor diamond treasury legacy']
      },
      {
        id: 'tg-3',
        name: 'Ramappa Temple (Kakatiya UNESCO Site)',
        state: 'Telangana',
        city: 'Palampet / Mulugu',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: '13th-century Kakatiya temple built with lightweight floating bricks, sandbox technology, and carved black basalt dancer bracket figures.',
        location: 'Palampet, Mulugu District',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 0,
        estimatedDuration: '2 hours',
        rating: 4.8,
        highlights: ['Lightweight floating bricks', 'Carved basalt dancer brackets', 'Sandbox seismic engineering']
      }
    ]
  },

  // 33. Tripura
  {
    id: 'tripura',
    name: 'Tripura',
    type: 'State',
    capital: 'Agartala',
    popularAirports: [{ code: 'IXA', name: 'Maharaja Bir Bikram Airport', city: 'Agartala' }],
    overview: 'Land of royal palaces and mystique: neoclassical white marble Ujjayanta Palace, floating Neermahal, and prehistoric Unakoti rock carvings.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Royal Palaces', 'Unakoti Rock Reliefs', 'Water Palaces', 'Bamboo Crafts'],
    popularActivities: ['Visiting Ujjayanta Palace museum', 'Boat ride to Neermahal', 'Exploring rock-cut Shiva carvings at Unakoti'],
    attractions: [
      {
        id: 'tr-1',
        name: 'Ujjayanta Palace & Museum',
        state: 'Tripura',
        city: 'Agartala',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Gleaming white neoclassical royal palace constructed in 1901 by Maharaja Radha Kishore Manikya, set within Mughal-style water gardens.',
        location: 'Palace Compound, Agartala',
        openingHours: '10:00 AM - 05:00 PM (Closed Mondays)',
        entryFee: 30,
        estimatedDuration: '2 hours',
        rating: 4.6,
        highlights: ['Curved central domes', 'Northeast ethnic lifestyle galleries', 'Musical fountains']
      },
      {
        id: 'tr-2',
        name: 'Neermahal Water Palace',
        state: 'Tripura',
        city: 'Melaghar',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80',
        description: 'Eastern India’s only lake palace, floating in the middle of Rudrasagar Lake blending Hindu and Islamic architectural motifs.',
        location: 'Rudrasagar Lake, Melaghar',
        openingHours: '09:00 AM - 05:00 PM',
        entryFee: 50,
        estimatedDuration: '2.5 hours',
        rating: 4.6,
        highlights: ['Speedboat approach on Rudrasagar lake', 'Moat-encircled royal chambers', 'Migratory water birds']
      },
      {
        id: 'tr-3',
        name: 'Unakoti Heritage Rock Carvings',
        state: 'Tripura',
        city: 'Kailashahar',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Mysterious ancient rock-relief gallery depicting one less than a crore (Unakoti) carved Shiva and Ganesha faces carved into a forested hillside.',
        location: 'Unakoti District, 178 km from Agartala',
        openingHours: '06:00 AM - 06:00 PM',
        entryFee: 20,
        estimatedDuration: '3 hours',
        rating: 4.7,
        highlights: ['30-ft tall Unakotiswara Kal Bhairava head', 'Jungle ravine stream setting', 'Prehistoric stone carvings']
      }
    ]
  },

  // 34. Uttar Pradesh
  {
    id: 'uttar-pradesh',
    name: 'Uttar Pradesh',
    type: 'State',
    capital: 'Lucknow',
    popularAirports: [
      { code: 'LKO', name: 'Chaudhary Charan Singh International Airport', city: 'Lucknow' },
      { code: 'VNS', name: 'Lal Bahadur Shastri International Airport', city: 'Varanasi' },
      { code: 'AYJ', name: 'Maharishi Valmiki International Airport', city: 'Ayodhya' }
    ],
    overview: 'Cultural heartland of India: eternal city Varanasi and Ganga Aarti, world wonder Taj Mahal in Agra, Awadhi Nawabi Lucknow, and Ayodhya.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Taj Mahal Wonder', 'Varanasi Ghats', 'Awadhi Cuisine', 'Spiritual Ayodhya'],
    popularActivities: ['Dawn boat ride on Ganges in Varanasi', 'Sunrise at Taj Mahal Agra', 'Bara Imambara labyrinth exploration'],
    attractions: [
      {
        id: 'up-1',
        name: 'Taj Mahal',
        state: 'Uttar Pradesh',
        city: 'Agra',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage wonder of the world, built in pure white Makrana marble by Shah Jahan in memory of Mumtaz Mahal on the Yamuna banks.',
        location: 'Dharmapuri, Forest Colony, Tajganj, Agra',
        openingHours: 'Sunrise to Sunset (Closed Fridays)',
        entryFee: 50,
        estimatedDuration: '3.5 hours',
        rating: 5.0,
        highlights: ['Pietra dura marble gemstone inlay', 'Perfect reflective symmetry', 'Yamuna river sunset backdrop']
      },
      {
        id: 'up-2',
        name: 'Varanasi Ghats & Ganga Maha Aarti',
        state: 'Uttar Pradesh',
        city: 'Varanasi',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=800&q=80',
        description: 'The ancient spiritual soul of India, where 84 stone ghats meet the holy river Ganga with mesmerizing evening brass-lamp Maha Aarti ceremonies.',
        location: 'Dashashwamedh Ghat, Varanasi',
        openingHours: '05:00 AM - 10:00 PM (Aarti at 06:45 PM)',
        entryFee: 0,
        estimatedDuration: '3 hours',
        rating: 4.9,
        highlights: ['Dashashwamedh Ghat evening aarti', 'Early morning sunrise wooden boat ride', 'Assi Ghat morning music yoga']
      },
      {
        id: 'up-3',
        name: 'Bara Imambara & Bhulbhulaiya',
        state: 'Uttar Pradesh',
        city: 'Lucknow',
        category: 'Architectural',
        image: 'https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?auto=format&fit=crop&w=800&q=80',
        description: 'Majestic 1784 monument built without any iron beams or pillars, housing the famous Bhulbhulaiya intricate 3D acoustic maze.',
        location: 'Machchhi Bhavan, Lucknow',
        openingHours: '06:00 AM - 05:00 PM',
        entryFee: 50,
        estimatedDuration: '2.5 hours',
        rating: 4.7,
        highlights: ['Bhulbhulaiya 1,024-passage maze', 'Asfi Mosque courtyard', 'Rumi Darwaza gateway view']
      }
    ]
  },

  // 35. Uttarakhand
  {
    id: 'uttarakhand',
    name: 'Uttarakhand',
    type: 'State',
    capital: 'Dehradun',
    popularAirports: [{ code: 'DED', name: 'Jolly Grant Airport', city: 'Dehradun / Rishikesh' }],
    overview: 'Devbhoomi (Land of the Gods): Yoga capital Rishikesh, sacred Kedarnath and Badrinath shrines, Jim Corbett tiger reserve, and Nainital lake.',
    bestSeason: 'Year-round (Char Dham May-Oct, Winter snow in Auli)',
    heroImage: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Yoga & Rafting Rishikesh', 'Char Dham Himalayan Shrines', 'Skiing in Auli', 'Tiger Safaris'],
    popularActivities: ['White water rafting in Rishikesh', 'Auli ropeway & ski slopes', 'Trek to Valley of Flowers'],
    attractions: [
      {
        id: 'uk-1',
        name: 'Rishikesh Lakshman Jhula & Triveni Ghat',
        state: 'Uttarakhand',
        city: 'Rishikesh',
        category: 'Adventure',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'World Capital of Yoga on the emerald Ganges foothills, famous for exhilarating grade-4 river rafting, ashrams, and Ganga Aarti.',
        location: 'Tapovan & Triveni Ghat, Rishikesh',
        openingHours: 'Open 24 hours',
        entryFee: 0,
        estimatedDuration: '3.5 hours',
        rating: 4.8,
        highlights: ['Ganges white-water rafting', 'Triveni Ghat evening Maha Aarti', 'Beatles Ashram exploration']
      },
      {
        id: 'uk-2',
        name: 'Kedarnath Temple',
        state: 'Uttarakhand',
        city: 'Rudraprayag',
        category: 'Religious',
        image: 'https://images.unsplash.com/photo-1600100397608-f010f444f434?auto=format&fit=crop&w=800&q=80',
        description: 'Sacred 8th-century Shiva temple of grey stone slabs perched dramatically at 11,755 ft against the snowbound Kedarnath peak.',
        location: 'Kedarnath Valley, Garhwal Himalayas',
        openingHours: '05:00 AM - 09:00 PM (May to November)',
        entryFee: 0,
        estimatedDuration: 'Full day trek/helicopter',
        rating: 5.0,
        highlights: ['Majestic Kedarnath peak backdrop', 'Ancient stone craftsmanship', 'Spiritual Himalayan ambiance']
      },
      {
        id: 'uk-3',
        name: 'Jim Corbett National Park',
        state: 'Uttarakhand',
        city: 'Ramnagar / Nainital',
        category: 'Wildlife',
        image: 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?auto=format&fit=crop&w=800&q=80',
        description: 'India’s oldest national park established in 1936, famed for royal Bengal tigers, wild elephant herds along the Ramganga river, and Sal forest drives.',
        location: 'Ramnagar, Nainital District',
        openingHours: '06:00 AM - 05:30 PM',
        entryFee: 500,
        estimatedDuration: '4 hours',
        rating: 4.8,
        highlights: ['Dhikala zone open jeep safari', 'Ramganga river elephant crossings', 'Colonial forest rest houses']
      }
    ]
  },

  // 36. West Bengal
  {
    id: 'west-bengal',
    name: 'West Bengal',
    type: 'State',
    capital: 'Kolkata',
    popularAirports: [{ code: 'CCU', name: 'Netaji Subhash Chandra Bose International Airport', city: 'Kolkata' }, { code: 'IXB', name: 'Bagdogra Airport', city: 'Siliguri / Darjeeling' }],
    overview: 'Cultural capital of India: Victoria Memorial and Howrah Bridge in Kolkata, UNESCO Darjeeling Himalayan Toy Train, and Sundarbans Royal Bengal tigers.',
    bestSeason: 'October to March',
    heroImage: 'https://images.unsplash.com/photo-1558431382-27e303142255?auto=format&fit=crop&w=1200&q=80',
    culturalTags: ['Colonial Architecture', 'Darjeeling Toy Train', 'Sundarbans Mangroves', 'Art & Literature'],
    popularActivities: ['Riding Darjeeling UNESCO toy train', 'Sunrise at Tiger Hill over Kanchenjunga', 'Heritage tram ride in Kolkata'],
    attractions: [
      {
        id: 'wb-1',
        name: 'Victoria Memorial & Howrah Bridge',
        state: 'West Bengal',
        city: 'Kolkata',
        category: 'Historical',
        image: 'https://images.unsplash.com/photo-1558431382-27e303142255?auto=format&fit=crop&w=800&q=80',
        description: 'Imposing white Makrana marble monument opened in 1921 set in 64 acres of gardens alongside the iconic cantilevered Howrah Bridge.',
        location: 'Queens Way, Maidan, Kolkata',
        openingHours: '10:00 AM - 05:00 PM (Gardens open 05:30 AM - 06:00 PM)',
        entryFee: 30,
        estimatedDuration: '3 hours',
        rating: 4.8,
        highlights: ['White marble dome and angel of victory', 'Royal gallery paintings', 'Evening laser projection show']
      },
      {
        id: 'wb-2',
        name: 'Darjeeling Himalayan Railway & Tiger Hill',
        state: 'West Bengal',
        city: 'Darjeeling',
        category: 'Natural',
        image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80',
        description: 'UNESCO World Heritage 2-ft narrow gauge steam toy train climbing through loops to Batasia, paired with sunrise views of Everest and Kanchenjunga.',
        location: 'Darjeeling Hill Town & Tiger Hill',
        openingHours: 'Toy train operates daily; Tiger Hill sunrise from 04:00 AM',
        entryFee: 1500,
        estimatedDuration: '4 hours',
        rating: 4.9,
        highlights: ['Golden sunrise over Mount Kanchenjunga', 'Batasia Loop spiral track', 'Vintage steam locomotive whistle']
      },
      {
        id: 'wb-3',
        name: 'Sundarbans Mangrove Tiger Reserve',
        state: 'West Bengal',
        city: 'Sundarbans',
        category: 'Wildlife',
        image: 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?auto=format&fit=crop&w=800&q=80',
        description: 'World’s largest coastal mangrove forest delta, inhabited by swimming royal Bengal tigers, estuarine crocodiles, and spotted deer.',
        location: 'South 24 Parganas District',
        openingHours: 'Boat cruises operate 07:00 AM - 04:30 PM',
        entryFee: 60,
        estimatedDuration: 'Full day boat tour',
        rating: 4.7,
        highlights: ['Cruising tidal creek mangroves', 'Watchtowers at Sajnekhali & Dobanki', 'Estuarine crocodile sightings']
      }
    ]
  }
];

export function getAllAttractions(): Attraction[] {
  return PAN_INDIA_DESTINATIONS.flatMap(d => d.attractions);
}

export function getAttractionsByState(stateName: string): Attraction[] {
  const dest = PAN_INDIA_DESTINATIONS.find(d => 
    d.name.toLowerCase().includes(stateName.toLowerCase()) || 
    stateName.toLowerCase().includes(d.name.toLowerCase())
  );
  return dest ? dest.attractions : [];
}

export function findDestinationByName(search: string): StateDestination | undefined {
  const term = search.toLowerCase();
  return PAN_INDIA_DESTINATIONS.find(d => 
    d.name.toLowerCase().includes(term) || 
    d.capital.toLowerCase().includes(term) ||
    d.attractions.some(a => a.name.toLowerCase().includes(term) || a.city.toLowerCase().includes(term))
  );
}

