# app/agents/retrieval_agent/utils.py
from pinecone import Pinecone
from dotenv import load_dotenv
import os

# Load .env file with encoding fallback
try:
    load_dotenv()
except UnicodeDecodeError:
    # Try UTF-16 encoding (common on Windows)
    try:
        load_dotenv(encoding='utf-16')
    except Exception:
        # Try UTF-16 with BOM
        try:
            load_dotenv(encoding='utf-16-le')
        except Exception:
            # If all encodings fail, continue without .env file
            pass

index_name = "intellisense-ai-dense-index"
cloud = "aws"
region = "us-east-1"
namespace = "Intellisense-namespace"

# Lazy initialization of Pinecone client and index
_pc = None
_index = None

def _get_pinecone_client():
    """Lazy initialization of Pinecone client"""
    global _pc
    if _pc is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError(
                "PINECONE_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment variables."
            )
        _pc = Pinecone(api_key=api_key)
    return _pc

def _get_index():
    """Lazy initialization of Pinecone index"""
    global _index
    if _index is None:
        pc = _get_pinecone_client()
        # Create index if missing
        if not pc.has_index(index_name):
            pc.create_index_for_model(
                name=index_name,
                cloud=cloud,
                region=region,
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"}  # chunk_text is the embedding field
                }
            )
        _index = pc.Index(index_name)
    return _index

# Create a module-level proxy that initializes the index lazily
class _LazyIndex:
    """Lazy proxy for Pinecone index that initializes on first access"""
    def _ensure_initialized(self):
        return _get_index()
    
    def __getattr__(self, name):
        return getattr(self._ensure_initialized(), name)
    
    def __call__(self, *args, **kwargs):
        return self._ensure_initialized()(*args, **kwargs)
    
    def search(self, *args, **kwargs):
        return self._ensure_initialized().search(*args, **kwargs)

# Export index as a lazy proxy
index = _LazyIndex()

# -----------------------------
# ORIGINAL RECORDS
# -----------------------------
records = [
    {"_id": "rec1", "chunk_text": "The Eiffel Tower was completed in 1889 and stands in Paris, France.", "source_type": "note", "source_url": "https://example.com/source1", "metadata": {"category": "history"}},
    {"_id": "rec2", "chunk_text": "Photosynthesis allows plants to convert sunlight into chemical energy.", "source_type": "note", "source_url": "https://example.com/source2", "metadata": {"category": "science"}},
    {"_id": "rec3", "chunk_text": "Albert Einstein developed the theory of relativity, transforming modern physics.", "source_type": "note", "source_url": "https://example.com/source3", "metadata": {"category": "science"}},
    {"_id": "rec4", "chunk_text": "The mitochondrion is responsible for producing ATP in eukaryotic cells.", "source_type": "note", "source_url": "https://example.com/source4", "metadata": {"category": "biology"}},
    {"_id": "rec5", "chunk_text": "Shakespeare's literary works include tragedies, comedies, and historical plays.", "source_type": "note", "source_url": "https://example.com/source5", "metadata": {"category": "literature"}},
    {"_id": "rec6", "chunk_text": "Under standard pressure, water boils at exactly 100 degrees Celsius.", "source_type": "note", "source_url": "https://example.com/source6", "metadata": {"category": "physics"}},
    {"_id": "rec7", "chunk_text": "The Great Wall of China stretches over 13,000 miles and was built for protection.", "source_type": "note", "source_url": "https://example.com/source7", "metadata": {"category": "history"}},
    {"_id": "rec8", "chunk_text": "Honey's low moisture and high acidity help it remain edible indefinitely.", "source_type": "note", "source_url": "https://example.com/source8", "metadata": {"category": "food science"}},
    {"_id": "rec9", "chunk_text": "Light travels approximately 299,792 kilometers per second in a vacuum.", "source_type": "note", "source_url": "https://example.com/source9", "metadata": {"category": "physics"}},
    {"_id": "rec10", "chunk_text": "Newton's three laws of motion describe the relationship between force and motion.", "source_type": "note", "source_url": "https://example.com/source10", "metadata": {"category": "physics"}},

    {"_id": "rec11", "chunk_text": "The human brain contains roughly 86 billion neurons.", "source_type": "note", "source_url": "https://example.com/source11", "metadata": {"category": "biology"}},
    {"_id": "rec12", "chunk_text": "Mars is known as the Red Planet due to iron oxide on its surface.", "source_type": "note", "source_url": "https://example.com/source12", "metadata": {"category": "astronomy"}},
    {"_id": "rec13", "chunk_text": "The Amazon rainforest produces about 20% of the world's oxygen.", "source_type": "note", "source_url": "https://example.com/source13", "metadata": {"category": "environment"}},
    {"_id": "rec14", "chunk_text": "Gravity is a fundamental force that attracts objects with mass toward each other.", "source_type": "note", "source_url": "https://example.com/source14", "metadata": {"category": "physics"}},
    {"_id": "rec15", "chunk_text": "The Roman Empire dominated much of Europe for over 500 years.", "source_type": "note", "source_url": "https://example.com/source15", "metadata": {"category": "history"}},
    {"_id": "rec16", "chunk_text": "Cells are the basic structural and functional units of living organisms.", "source_type": "note", "source_url": "https://example.com/source16", "metadata": {"category": "biology"}},
    {"_id": "rec17", "chunk_text": "Volcanoes form when magma rises to the Earth's surface.", "source_type": "note", "source_url": "https://example.com/source17", "metadata": {"category": "geology"}},
    {"_id": "rec18", "chunk_text": "The heart pumps blood throughout the body using a system of arteries and veins.", "source_type": "note", "source_url": "https://example.com/source18", "metadata": {"category": "biology"}},
    {"_id": "rec19", "chunk_text": "Binary code represents chunk_text or instructions using only zeros and ones.", "source_type": "note", "source_url": "https://example.com/source19", "metadata": {"category": "technology"}},
    {"_id": "rec20", "chunk_text": "The Pythagorean theorem states that a^2 + b^2 = c^2 in right triangles.", "source_type": "note", "source_url": "https://example.com/source20", "metadata": {"category": "mathematics"}},

    {"_id": "rec21", "chunk_text": "Ocean tides are primarily caused by the gravitational pull of the moon.", "source_type": "note", "source_url": "https://example.com/source21", "metadata": {"category": "earth science"}},
    {"_id": "rec22", "chunk_text": "Protein synthesis occurs in ribosomes within living cells.", "source_type": "note", "source_url": "https://example.com/source22", "metadata": {"category": "biology"}},
    {"_id": "rec23", "chunk_text": "The Internet is a global network of interconnected computers.", "source_type": "note", "source_url": "https://example.com/source23", "metadata": {"category": "technology"}},
    {"_id": "rec24", "chunk_text": "The Mona Lisa was painted by Leonardo da Vinci in the early 16th century.", "source_type": "note", "source_url": "https://example.com/source24", "metadata": {"category": "art"}},
    {"_id": "rec25", "chunk_text": "Earth orbits the sun at an average distance of 93 million miles.", "source_type": "note", "source_url": "https://example.com/source25", "metadata": {"category": "astronomy"}},
    {"_id": "rec26", "chunk_text": "The respiratory system enables gas exchange between the body and the environment.", "source_type": "note", "source_url": "https://example.com/source26", "metadata": {"category": "biology"}},
    {"_id": "rec27", "chunk_text": "Friction is a force that opposes the motion of objects in contact.", "source_type": "note", "source_url": "https://example.com/source27", "metadata": {"category": "physics"}},
    {"_id": "rec28", "chunk_text": "Electricity flows through conductors such as copper and aluminum.", "source_type": "note", "source_url": "https://example.com/source28", "metadata": {"category": "physics"}},
    {"_id": "rec29", "chunk_text": "Clouds form when water vapor condenses into tiny droplets.", "source_type": "note", "source_url": "https://example.com/source29", "metadata": {"category": "weather"}},
    {"_id": "rec30", "chunk_text": "The periodic table organizes elements by increasing atomic number.", "source_type": "note", "source_url": "https://example.com/source30", "metadata": {"category": "chemistry"}},

    {"_id": "rec31", "chunk_text": "Bacteria are single-celled microorganisms found in almost every habitat on Earth.", "source_type": "note", "source_url": "https://example.com/source31", "metadata": {"category": "biology"}},
    {"_id": "rec32", "chunk_text": "Solar panels convert sunlight into electricity using photovoltaic cells.", "source_type": "note", "source_url": "https://example.com/source32", "metadata": {"category": "energy"}},
    {"_id": "rec33", "chunk_text": "Gravity causes objects to accelerate downward at 9.8 m/s² on Earth.", "source_type": "note", "source_url": "https://example.com/source33", "metadata": {"category": "physics"}},
    {"_id": "rec34", "chunk_text": "Algorithms are step-by-step instructions used to solve problems.", "source_type": "note", "source_url": "https://example.com/source34", "metadata": {"category": "computer science"}},
    {"_id": "rec35", "chunk_text": "Rainbows are formed when light is refracted, reflected, and dispersed by water droplets.", "source_type": "note", "source_url": "https://example.com/source35", "metadata": {"category": "optics"}},
    {"_id": "rec36", "chunk_text": "The Nile River is the longest river in the world.", "source_type": "note", "source_url": "https://example.com/source36", "metadata": {"category": "geography"}},
    {"_id": "rec37", "chunk_text": "Earth’s atmosphere is composed primarily of nitrogen and oxygen.", "source_type": "note", "source_url": "https://example.com/source37", "metadata": {"category": "earth science"}},
    {"_id": "rec38", "chunk_text": "DNA stores genetic information in the form of a double helix.", "source_type": "note", "source_url": "https://example.com/source38", "metadata": {"category": "genetics"}},
    {"_id": "rec39", "chunk_text": "Pluto was reclassified as a dwarf planet in 2006.", "source_type": "note", "source_url": "https://example.com/source39", "metadata": {"category": "astronomy"}},
    {"_id": "rec40", "chunk_text": "The Pacific Ocean is the largest and deepest ocean on Earth.", "source_type": "note", "source_url": "https://example.com/source40", "metadata": {"category": "geography"}},

    {"_id": "rec41", "chunk_text": "A chemical reaction occurs when substances interact to form new products.", "source_type": "note", "source_url": "https://example.com/source41", "metadata": {"category": "chemistry"}},
    {"_id": "rec42", "chunk_text": "The speed of sound is about 343 meters per second in air at room temperature.", "source_type": "note", "source_url": "https://example.com/source42", "metadata": {"category": "physics"}},
    {"_id": "rec43", "chunk_text": "The Sahara Desert is the largest hot desert in the world.", "source_type": "note", "source_url": "https://example.com/source43", "metadata": {"category": "geography"}},
    {"_id": "rec44", "chunk_text": "The immune system protects the body from harmful pathogens.", "source_type": "note", "source_url": "https://example.com/source44", "metadata": {"category": "biology"}},
    {"_id": "rec45", "chunk_text": "Magnetism is a force created by moving electric charges.", "source_type": "note", "source_url": "https://example.com/source45", "metadata": {"category": "physics"}},
    {"_id": "rec46", "chunk_text": "Comets are icy celestial bodies that develop glowing comas when near the sun.", "source_type": "note", "source_url": "https://example.com/source46", "metadata": {"category": "astronomy"}},
    {"_id": "rec47", "chunk_text": "Antibiotics are medications that kill or inhibit bacterial growth.", "source_type": "note", "source_url": "https://example.com/source47", "metadata": {"category": "medicine"}},
    {"_id": "rec48", "chunk_text": "Machine learning enables computers to learn patterns from data.", "source_type": "note", "source_url": "https://example.com/source48", "metadata": {"category": "technology"}},
    {"_id": "rec49", "chunk_text": "The Renaissance marked a period of revival in art and science in Europe.", "source_type": "note", "source_url": "https://example.com/source49", "metadata": {"category": "history"}},
    {"_id": "rec50", "chunk_text": "The Fibonacci sequence is a series of numbers where each number is the sum of the previous two.", "source_type": "note", "source_url": "https://example.com/source50", "metadata": {"category": "mathematics"}},

    {"_id": "rec51", "chunk_text": "Wind energy is generated using turbines that convert kinetic energy into electricity.", "source_type": "note", "source_url": "https://example.com/source51", "metadata": {"category": "energy"}},
    {"_id": "rec52", "chunk_text": "Plate tectonics explain the movement of Earth's lithospheric plates.", "source_type": "note", "source_url": "https://example.com/source52", "metadata": {"category": "geology"}},
    {"_id": "rec53", "chunk_text": "The circulatory system transports oxygen and nutrients throughout the body.", "source_type": "note", "source_url": "https://example.com/source53", "metadata": {"category": "biology"}},
    {"_id": "rec54", "chunk_text": "Artificial intelligence enables machines to perform tasks that normally require human intelligence.", "source_type": "note", "source_url": "https://example.com/source54", "metadata": {"category": "technology"}},
    {"_id": "rec55", "chunk_text": "Saturn is known for its large system of icy rings.", "source_type": "note", "source_url": "https://example.com/source55", "metadata": {"category": "astronomy"}},
]

# ---------------------------------------
# FIX: CLEAN AND FLATTEN ALL RECORDS
# ---------------------------------------
# clean_records = []
# for r in records:
#     clean_records.append({
#         "_id": r["_id"],
#         "chunk_text": r["chunk_text"],
#         "source_type": r["source_type"],
#         "source_url": r["source_url"],
#         "category": r["metadata"]["category"]  # move metadata to top level
#     })

# # Upload to Pinecone
# Note: index is now lazily initialized via _LazyIndex proxy above
# index.upsert_records(namespace, clean_records)

# # print(index.describe_index_stats())
# query = "What is physics"

# # Search the dense index
# results = index.search(
#     namespace="Intellisense-namespace",
#     query={
#         "top_k": 10,
#         "inputs": {
#             'text': query
#         }
#     }
# )
# print(results)



# Do Not Disturb the Above Code it is for testing
