# backend/chatbot.py
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import pathlib

@dataclass
class SubjectTopic:
    subject: str
    topics: List[str]
    difficulty: str  # 'basic', 'intermediate', 'advanced'

@dataclass
class ChatbotResponse:
    message: str
    recommendations: List[Dict]
    study_plan: List[SubjectTopic]
    confidence: float

class EducationChatbot:
    def __init__(self, majors_kb_path: str, student_data_path: Optional[str] = None):
        self.majors_kb = self._load_majors_kb(majors_kb_path)
        self.student_data = self._load_student_data(student_data_path) if student_data_path else None
        self.curriculum_map = self._init_curriculum_map()
        self.university_aliases = self._init_university_aliases()
        
    def _init_university_aliases(self) -> Dict[str, str]:
        """Initialize university name aliases and abbreviations"""
        return {
            # Universitas Negeri
            'ui': 'Universitas Indonesia',
            'universitas indonesia': 'Universitas Indonesia',
            'itb': 'Institut Teknologi Bandung',
            'institut teknologi bandung': 'Institut Teknologi Bandung',
            'ugm': 'Universitas Gadjah Mada',
            'universitas gadjah mada': 'Universitas Gadjah Mada',
            'its': 'Institut Teknologi Sepuluh Nopember',
            'institut teknologi sepuluh nopember': 'Institut Teknologi Sepuluh Nopember',
            'ipb': 'Institut Pertanian Bogor',
            'institut pertanian bogor': 'Institut Pertanian Bogor',
            'undip': 'Universitas Diponegoro',
            'universitas diponegoro': 'Universitas Diponegoro',
            'unair': 'Universitas Airlangga',
            'universitas airlangga': 'Universitas Airlangga',
            'unsri': 'Universitas Sriwijaya',
            'universitas sriwijaya': 'Universitas Sriwijaya',
            'unhas': 'Universitas Hasanuddin',
            'universitas hasanuddin': 'Universitas Hasanuddin',
            'unpad': 'Universitas Padjadjaran',
            'universitas padjadjaran': 'Universitas Padjadjaran',
            'uns': 'Universitas Sebelas Maret',
            'universitas sebelas maret': 'Universitas Sebelas Maret',
            'upi': 'Universitas Pendidikan Indonesia',
            'universitas pendidikan indonesia': 'Universitas Pendidikan Indonesia',
            'unesa': 'Universitas Negeri Surabaya',
            'universitas negeri surabaya': 'Universitas Negeri Surabaya',
            'uny': 'Universitas Negeri Yogyakarta',
            'universitas negeri yogyakarta': 'Universitas Negeri Yogyakarta',
            'unm': 'Universitas Negeri Makassar',
            'universitas negeri makassar': 'Universitas Negeri Makassar',
            'unp': 'Universitas Negeri Padang',
            'universitas negeri padang': 'Universitas Negeri Padang',
            'um': 'Universitas Negeri Malang',
            'universitas negeri malang': 'Universitas Negeri Malang',
            'unej': 'Universitas Jember',
            'universitas jember': 'Universitas Jember',
            'unsoed': 'Universitas Jenderal Soedirman',
            'universitas jenderal soedirman': 'Universitas Jenderal Soedirman',
            'untirta': 'Universitas Sultan Ageng Tirtayasa',
            'universitas sultan ageng tirtayasa': 'Universitas Sultan Ageng Tirtayasa',
            'untan': 'Universitas Tanjungpura',
            'universitas tanjungpura': 'Universitas Tanjungpura',
            'unsyiah': 'Universitas Syiah Kuala',
            'universitas syiah kuala': 'Universitas Syiah Kuala',
            'unand': 'Universitas Andalas',
            'universitas andalas': 'Universitas Andalas',
            'unri': 'Universitas Riau',
            'universitas riau': 'Universitas Riau',
            'usu': 'Universitas Sumatera Utara',
            'universitas sumatera utara': 'Universitas Sumatera Utara',
            
            # Institut dan Politeknik
            'itn': 'Institut Teknologi Nasional',
            'itenas': 'Institut Teknologi Nasional',
            'itera': 'Institut Teknologi Sumatera',
            'institut teknologi sumatera': 'Institut Teknologi Sumatera',
            'pens': 'Politeknik Elektronika Negeri Surabaya',
            'politeknik elektronika negeri surabaya': 'Politeknik Elektronika Negeri Surabaya',
            'pnj': 'Politeknik Negeri Jakarta',
            'politeknik negeri jakarta': 'Politeknik Negeri Jakarta',
            
            # Universitas Swasta Terkenal
            'uph': 'Universitas Pelita Harapan',
            'universitas pelita harapan': 'Universitas Pelita Harapan',
            'binus': 'Bina Nusantara University',
            'bina nusantara': 'Bina Nusantara University',
            'trisakti': 'Universitas Trisakti',
            'universitas trisakti': 'Universitas Trisakti',
            'atmajaya': 'Universitas Katolik Indonesia Atma Jaya',
            'unika atma jaya': 'Universitas Katolik Indonesia Atma Jaya',
            'tarumanagara': 'Universitas Tarumanagara',
            'universitas tarumanagara': 'Universitas Tarumanagara',
            'untar': 'Universitas Tarumanagara',
            'paramadina': 'Universitas Paramadina',
            'universitas paramadina': 'Universitas Paramadina',
        }
        
    def _load_majors_kb(self, path: str) -> Dict:
        """Load majors knowledge base"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading majors KB: {e}")
            return {}
    
    def _load_student_data(self, path: str) -> Optional[pd.DataFrame]:
        """Load student historical data from Excel"""
        try:
            return pd.read_excel(path)
        except Exception as e:
            print(f"Error loading student data: {e}")
            return None
    
    def _init_curriculum_map(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize subject-topic mapping based on Indonesian SMA curriculum"""
        return {
            "saintek": {
                "matematika": [
                    "Fungsi, Komposisi, dan Invers",
                    "Persamaan dan Pertidaksamaan",
                    "Sistem Persamaan Linear",
                    "Matriks dan Determinan",
                    "Program Linear",
                    "Barisan dan Deret",
                    "Limit Fungsi",
                    "Turunan dan Aplikasinya",
                    "Integral dan Aplikasinya",
                    "Trigonometri",
                    "Dimensi Tiga",
                    "Vektor",
                    "Statistika dan Peluang"
                ],
                "fisika": [
                    "Besaran dan Satuan",
                    "Kinematika Gerak",
                    "Dinamika Partikel",
                    "Usaha dan Energi",
                    "Momentum dan Impuls",
                    "Rotasi dan Kesetimbangan Benda Tegar",
                    "Elastisitas dan Hukum Hooke",
                    "Fluida Statis dan Dinamis",
                    "Suhu dan Kalor",
                    "Termodinamika",
                    "Gelombang Mekanik",
                    "Bunyi",
                    "Cahaya dan Optik",
                    "Listrik Statis",
                    "Listrik Dinamis",
                    "Kemagnetan",
                    "Induksi Elektromagnetik",
                    "Arus Bolak-balik",
                    "Radiasi Benda Hitam",
                    "Teori Kuantum",
                    "Fisika Atom dan Inti"
                ],
                "kimia": [
                    "Struktur Atom dan Tabel Periodik",
                    "Ikatan Kimia",
                    "Bentuk Molekul",
                    "Stoikiometri",
                    "Larutan",
                    "Reaksi Redoks",
                    "Termokimia",
                    "Laju Reaksi",
                    "Kesetimbangan Kimia",
                    "Kesetimbangan Ion dan pH",
                    "Larutan Penyangga",
                    "Hidrolisis Garam",
                    "Kelarutan dan Hasil Kali Kelarutan",
                    "Elektrokimia",
                    "Kimia Unsur",
                    "Senyawa Karbon",
                    "Benzena dan Turunannya",
                    "Makromolekul"
                ],
                "biologi": [
                    "Keanekaragaman Hayati",
                    "Virus",
                    "Archaebacteria dan Eubacteria",
                    "Protista",
                    "Fungi",
                    "Plantae",
                    "Animalia",
                    "Ekosistem",
                    "Sel sebagai Unit Kehidupan",
                    "Biomolekul",
                    "Katabolisme dan Anabolisme",
                    "Genetika",
                    "Mutasi",
                    "Evolusi",
                    "Bioteknologi",
                    "Sistem Organ pada Manusia",
                    "Reproduksi dan Perkembangan"
                ],
                "bahasa_indonesia": [
                    "Teks Laporan Hasil Observasi",
                    "Teks Eksposisi",
                    "Teks Anekdot",
                    "Teks Hikayat",
                    "Teks Negosiasi",
                    "Teks Debat",
                    "Teks Biografi",
                    "Puisi",
                    "Hikayat",
                    "Novel",
                    "Drama",
                    "Kritik dan Esai",
                    "Resensi"
                ],
                "bahasa_inggris": [
                    "Expression and Greeting",
                    "Congratulation and Compliment",
                    "Asking and Giving Opinion",
                    "Suggestion and Offer",
                    "Announcement",
                    "Recount Text",
                    "Narrative Text",
                    "Descriptive Text",
                    "News Item",
                    "Analytical Exposition",
                    "Hortatory Exposition",
                    "Explanation Text",
                    "Discussion Text",
                    "Review Text"
                ]
            },
            "soshum": {
                "matematika": [
                    "Bilangan Real",
                    "Persamaan dan Pertidaksamaan Linear",
                    "Sistem Persamaan Linear Dua Variabel",
                    "Fungsi Kuadrat",
                    "Matematika Keuangan",
                    "Barisan dan Deret Aritmatika",
                    "Barisan dan Deret Geometri",
                    "Statistika Deskriptif",
                    "Peluang",
                    "Kombinatorika"
                ],
                "ekonomi": [
                    "Ilmu Ekonomi dan Masalah Ekonomi",
                    "Sistem Ekonomi",
                    "Kebutuhan dan Alat Pemuas Kebutuhan",
                    "Perilaku Konsumen dan Produsen",
                    "Pasar dan Terbentuknya Harga",
                    "Elastisitas dan Penerapannya",
                    "Konsep Produksi",
                    "Biaya Produksi",
                    "Pendapatan Nasional",
                    "Pertumbuhan dan Pembangunan Ekonomi",
                    "Ketenagakerjaan",
                    "APBN dan APBD",
                    "Perpajakan",
                    "Uang dan Lembaga Keuangan",
                    "Kebijakan Moneter dan Fiskal",
                    "Perdagangan Internasional",
                    "Neraca Pembayaran",
                    "Kerjasama Ekonomi Internasional",
                    "Akuntansi sebagai Sistem Informasi",
                    "Persamaan Dasar Akuntansi",
                    "Siklus Akuntansi",
                    "Akuntansi Perusahaan Dagang",
                    "Manajemen dan Badan Usaha",
                    "Kewirausahaan"
                ],
                "geografi": [
                    "Pengetahuan Dasar Geografi",
                    "Penelitian Geografi",
                    "Langkah Penelitian Geografi",
                    "Dinamika Planet Bumi",
                    "Hubungan Matahari, Bumi, dan Bulan",
                    "Lapisan Bumi",
                    "Lithosfer dan Pedosfer",
                    "Atmosfer dan Hidrosfer",
                    "Biosfer",
                    "Antroposfer",
                    "Sumber Daya Alam",
                    "Ketahanan Pangan, Industri, dan Energi",
                    "Kearifan dalam Pemanfaatan SDA",
                    "Mitigasi dan Adaptasi Bencana Alam",
                    "Dinamika Kependudukan",
                    "Keragaman Budaya Indonesia",
                    "Ketahanan Pangan Nasional",
                    "Industri dan Pertanian",
                    "Transportasi dan Tata Guna Lahan",
                    "Interaksi Keruangan Desa dan Kota"
                ],
                "sejarah": [
                    "Konsep Berpikir Sejarah",
                    "Penelitian Sejarah",
                    "Peradaban Awal Dunia",
                    "Peradaban Awal Masyarakat Indonesia",
                    "Perkembangan Negara-negara Tradisional",
                    "Indonesia Zaman Hindu-Buddha",
                    "Perkembangan Islam di Dunia",
                    "Perkembangan Islam di Indonesia",
                    "Revolusi Dunia dan Pengaruhnya",
                    "Kolonialisme dan Imperialisme",
                    "Pergerakan Nasional Indonesia",
                    "Proklamasi dan Perkembangan Negara",
                    "Dinasti Abbasiyah",
                    "Perang Dunia dan Dampaknya",
                    "Proklamasi Kemerdekaan RI",
                    "Perkembangan Negara Kebangsaan",
                    "Sistem dan Struktur Politik-Ekonomi Indonesia",
                    "Kehidupan Politik dan Ekonomi Bangsa Indonesia",
                    "Peran Bangsa Indonesia dalam Perdamaian Dunia"
                ],
                "sosiologi": [
                    "Fungsi Sosiologi untuk Mengenali Gejala Sosial",
                    "Individu, Kelompok, dan Hubungan Sosial",
                    "Ragam Gejala Sosial dalam Masyarakat",
                    "Rancangan Penelitian Sosial",
                    "Pembentukan Kelompok Sosial",
                    "Permasalahan Sosial dalam Masyarakat",
                    "Perbedaan, Kesetaraan, dan Harmoni Sosial",
                    "Konflik dan Integrasi dalam Kehidupan Sosial",
                    "Kearifan Lokal dan Pemberdayaan Komunitas",
                    "Ketimpangan Sosial sebagai Dampak Perubahan",
                    "Globalisasi dan Perubahan Komunitas Lokal",
                    "Penelitian Sosial dan Metode Penelitian"
                ],
                "bahasa_indonesia": [
                    "Teks Laporan Hasil Observasi",
                    "Teks Eksposisi",
                    "Teks Anekdot",
                    "Teks Hikayat",
                    "Teks Negosiasi",
                    "Teks Debat",
                    "Teks Biografi",
                    "Puisi",
                    "Hikayat",
                    "Novel",
                    "Drama",
                    "Kritik dan Esai",
                    "Resensi"
                ],
                "bahasa_inggris": [
                    "Expression and Greeting",
                    "Congratulation and Compliment",
                    "Asking and Giving Opinion",
                    "Suggestion and Offer",
                    "Announcement",
                    "Recount Text",
                    "Narrative Text",
                    "Descriptive Text",
                    "News Item",
                    "Analytical Exposition",
                    "Hortatory Exposition",
                    "Explanation Text",
                    "Discussion Text",
                    "Review Text"
                ]
            }
        }
    
    def extract_grades_from_text(self, text: str) -> Dict[str, float]:
        """Extract grade information from user input"""
        grades = {}
        
        # Pattern untuk menangkap nilai dengan berbagai format
        patterns = [
            (r'matematika[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'matematika'),
            (r'fisika[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'fisika'),
            (r'kimia[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'kimia'),
            (r'biologi[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'biologi'),
            (r'ekonomi[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'ekonomi'),
            (r'geografi[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'geografi'),
            (r'sejarah[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'sejarah'),
            (r'sosiologi[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'sosiologi'),
            (r'bahasa\s*indonesia[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'bahasa_indonesia'),
            (r'bahasa\s*inggris[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'bahasa_inggris'),
            (r'(?:rata[:\s-]*rata|rapor)[:\s]*(?:nilai\s*)?(\d+(?:[.,]\d+)?)', 'rata_rata'),
            (r'(?:nilai\s+)?(\d+(?:[.,]\d+)?)[:\s]*matematika', 'matematika'),
            (r'(?:nilai\s+)?(\d+(?:[.,]\d+)?)[:\s]*fisika', 'fisika'),
            (r'(?:nilai\s+)?(\d+(?:[.,]\d+)?)[:\s]*kimia', 'kimia'),
            (r'(?:nilai\s+)?(\d+(?:[.,]\d+)?)[:\s]*biologi', 'biologi')
        ]
        
        text_lower = text.lower()
        
        for pattern, subject in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value_str = match.group(1).replace(',', '.')
                try:
                    value = float(value_str)
                    if 0 <= value <= 100:  # Validasi range nilai
                        grades[subject] = value
                except ValueError:
                    continue
        
        return grades
    
    def detect_intent(self, text: str) -> str:
        """Detect user intent from input text with improved logic"""
        text_lower = text.lower()
        
        # Check for grade information first
        grades = self.extract_grades_from_text(text)
        has_grades = len(grades) > 0
        
        # Keywords for different intents
        major_target_keywords = ['ingin', 'mau', 'pengen', 'target', 'cita-cita', 'impian', 'masuk']
        major_info_keywords = ['cocok', 'sesuai', 'rekomendasi', 'saran', 'jurusan apa']
        study_keywords = ['belajar', 'tips', 'cara', 'strategi', 'meningkatkan', 'persiapan', 'utbk']
        info_keywords = ['info', 'informasi', 'passing grade', 'persyaratan', 'syarat']
        
        # Specific major detection
        major_mentioned = self._extract_major_from_text(text)
        university_mentioned = self._extract_university_from_text(text)
        
        # Intent decision logic
        if has_grades and any(keyword in text_lower for keyword in major_info_keywords):
            return 'grade_to_major'
        elif any(keyword in text_lower for keyword in major_target_keywords) and (major_mentioned or university_mentioned):
            return 'major_preparation'
        elif any(keyword in text_lower for keyword in study_keywords):
            return 'study_tips'
        elif any(keyword in text_lower for keyword in info_keywords) and (major_mentioned or university_mentioned):
            return 'major_info'
        elif major_mentioned and not has_grades:
            return 'major_preparation'
        elif has_grades:
            return 'grade_to_major'
        else:
            return 'general'
    
    def _extract_university_from_text(self, text: str) -> str:
        """Extract university name from text using aliases"""
        text_lower = text.lower()
        
        # Check aliases first (shorter matches)
        for alias, full_name in self.university_aliases.items():
            if alias in text_lower:
                return full_name
        
        # Check for university patterns
        university_patterns = [
            r'universitas\s+([a-zA-Z\s]+)',
            r'institut\s+([a-zA-Z\s]+)',
            r'politeknik\s+([a-zA-Z\s]+)',
            r'sekolah\s+tinggi\s+([a-zA-Z\s]+)'
        ]
        
        for pattern in university_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).title()
        
        return ""
    
    def _get_major_list(self) -> List[str]:
        """Get list of major names for detection"""
        majors = ['informatika', 'kedokteran', 'teknik', 'ekonomi', 'hukum', 'psikologi', 
                 'komunikasi', 'manajemen', 'akuntansi', 'farmasi', 'arsitektur']
        return majors
    
    def recommend_majors_by_grades(self, grades: Dict[str, float], program: str = None) -> List[Dict]:
        """Recommend majors based on current grades"""
        recommendations = []
        
        # Calculate average if not provided
        if 'rata_rata' not in grades:
            grade_values = [v for k, v in grades.items() if k != 'rata_rata']
            if grade_values:
                grades['rata_rata'] = sum(grade_values) / len(grade_values)
        
        avg_grade = grades.get('rata_rata', 75)
        
        # Determine program automatically if not specified
        if not program:
            program = self._determine_program_from_grades(grades)
        
        # Filter majors based on KB data
        for key, major_data in self.majors_kb.items():
            # Skip if no relevant data
            if not major_data.get('university') or not major_data.get('major'):
                continue
                
            # Determine major program type
            major_name = major_data.get('major', '').lower()
            major_program = self._determine_program_from_major(major_name)
            
            # Skip if program doesn't match
            if program != 'unknown' and major_program != 'unknown' and program != major_program:
                continue
            
            # Calculate recommendation score
            recommendation = self._calculate_recommendation_score(major_data, grades, avg_grade)
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by probability and limit results
        recommendations.sort(key=lambda x: x['probability'], reverse=True)
        return recommendations[:15]
    
    def _determine_program_from_grades(self, grades: Dict[str, float]) -> str:
        """Determine program based on available grades"""
        saintek_subjects = ['matematika', 'fisika', 'kimia', 'biologi']
        soshum_subjects = ['ekonomi', 'geografi', 'sejarah', 'sosiologi']
        
        saintek_count = sum(1 for subj in saintek_subjects if subj in grades)
        soshum_count = sum(1 for subj in soshum_subjects if subj in grades)
        
        if saintek_count > soshum_count:
            return 'saintek'
        elif soshum_count > saintek_count:
            return 'soshum'
        else:
            return 'saintek'  # Default to saintek
    
    def _calculate_recommendation_score(self, major_data: Dict, grades: Dict[str, float], avg_grade: float) -> Optional[Dict]:
        """Calculate recommendation score for a major"""
        # Get required average from KB (if available)
        required_rapor = major_data.get('required_rapor')
        passing_grade = major_data.get('passing_grade')
        acceptance_rate = major_data.get('acceptance_rate')
        
        # Use multiple criteria for scoring
        base_score = avg_grade
        
        # Calculate probability based on multiple factors
        probability = 0.5  # Base probability
        
        # Factor 1: Rapor requirement
        if required_rapor:
            grade_diff = avg_grade - required_rapor
            if grade_diff >= 0:
                probability += min(0.4, grade_diff / 50)  # Max 0.4 bonus
            else:
                probability += max(-0.3, grade_diff / 50)  # Max 0.3 penalty
        
        # Factor 2: Acceptance rate
        if acceptance_rate:
            if acceptance_rate > 20:
                probability += 0.1
            elif acceptance_rate < 5:
                probability -= 0.2
        
        # Factor 3: Subject-specific bonus
        major_name = major_data.get('major', '').lower()
        subject_bonus = self._get_subject_bonus(major_name, grades)
        probability += subject_bonus
        
        # Clamp probability between 0.05 and 0.95
        probability = max(0.05, min(0.95, probability))
        
        # Determine category
        if probability >= 0.8:
            category = "Sangat Memungkinkan"
        elif probability >= 0.6:
            category = "Memungkinkan"
        elif probability >= 0.4:
            category = "Cukup Memungkinkan"
        elif probability >= 0.2:
            category = "Kurang Memungkinkan"
        else:
            category = "Sulit"
        
        return {
            'university': major_data.get('university'),
            'major': major_data.get('major'),
            'required_rapor': required_rapor,
            'current_gap': round((required_rapor or avg_grade) - avg_grade, 2),
            'probability': round(probability, 3),
            'category': category,
            'acceptance_rate': acceptance_rate,
            'passing_grade': passing_grade,
            'program': self._determine_program_from_major(major_data.get('major', ''))
        }
    
    def _get_subject_bonus(self, major_name: str, grades: Dict[str, float]) -> float:
        """Calculate subject-specific bonus for major recommendation"""
        bonus = 0.0
        
        # Subject relevance mapping
        if 'teknik' in major_name or 'informatika' in major_name:
            if 'matematika' in grades and grades['matematika'] >= 85:
                bonus += 0.15
            if 'fisika' in grades and grades['fisika'] >= 80:
                bonus += 0.1
        elif 'kedokteran' in major_name or 'farmasi' in major_name:
            if 'biologi' in grades and grades['biologi'] >= 85:
                bonus += 0.15
            if 'kimia' in grades and grades['kimia'] >= 80:
                bonus += 0.1
        elif 'ekonomi' in major_name or 'manajemen' in major_name:
            if 'matematika' in grades and grades['matematika'] >= 80:
                bonus += 0.1
            if 'ekonomi' in grades and grades['ekonomi'] >= 85:
                bonus += 0.15
        elif 'hukum' in major_name:
            if 'bahasa_indonesia' in grades and grades['bahasa_indonesia'] >= 85:
                bonus += 0.15
        
        return min(bonus, 0.2)  # Max 0.2 bonus
    
    def get_study_plan_for_major(self, major_name: str, program: str = 'saintek') -> List[SubjectTopic]:
        """Generate study plan for specific major"""
        study_plan = []
        
        # Get curriculum for the program
        curriculum = self.curriculum_map.get(program, {})
        
        # Major-specific subject priorities
        major_subjects = self._get_priority_subjects_for_major(major_name.lower(), program)
        
        for subject, priority in major_subjects.items():
            if subject in curriculum:
                difficulty = 'advanced' if priority == 'high' else 'intermediate' if priority == 'medium' else 'basic'
                
                # Get relevant topics based on major
                topics = self._filter_topics_for_major(subject, curriculum[subject], major_name.lower())
                
                study_plan.append(SubjectTopic(
                    subject=subject,
                    topics=topics,
                    difficulty=difficulty
                ))
        
        return study_plan
    
    def _get_priority_subjects_for_major(self, major_name: str, program: str) -> Dict[str, str]:
        """Get priority subjects for specific major"""
        # Enhanced major-subject mappings
        major_mappings = {
            'saintek': {
                'teknik': {'matematika': 'high', 'fisika': 'high', 'bahasa_inggris': 'medium'},
                'informatika': {'matematika': 'high', 'fisika': 'medium', 'bahasa_inggris': 'high'},
                'kedokteran': {'biologi': 'high', 'kimia': 'high', 'fisika': 'medium', 'matematika': 'medium'},
                'farmasi': {'kimia': 'high', 'biologi': 'high', 'matematika': 'medium'},
                'arsitektur': {'matematika': 'high', 'fisika': 'high', 'bahasa_inggris': 'medium'},
                'biologi': {'biologi': 'high', 'kimia': 'medium', 'matematika': 'medium'},
                'kimia': {'kimia': 'high', 'matematika': 'high', 'fisika': 'medium'},
                'fisika': {'fisika': 'high', 'matematika': 'high'},
                'matematika': {'matematika': 'high', 'fisika': 'medium'},
                'default': {'matematika': 'high', 'fisika': 'medium', 'kimia': 'medium', 'biologi': 'medium', 'bahasa_indonesia': 'basic', 'bahasa_inggris': 'basic'}
            },
            'soshum': {
                'ekonomi': {'matematika': 'high', 'ekonomi': 'high', 'bahasa_inggris': 'medium'},
                'hukum': {'bahasa_indonesia': 'high', 'sejarah': 'medium', 'sosiologi': 'medium'},
                'komunikasi': {'bahasa_indonesia': 'high', 'bahasa_inggris': 'high', 'sosiologi': 'medium'},
                'psikologi': {'matematika': 'medium', 'sosiologi': 'high', 'bahasa_indonesia': 'medium'},
                'administrasi': {'ekonomi': 'high', 'sosiologi': 'medium', 'bahasa_indonesia': 'medium'},
                'hubungan internasional': {'bahasa_inggris': 'high', 'sejarah': 'high', 'geografi': 'medium'},
                'manajemen': {'matematika': 'high', 'ekonomi': 'high', 'bahasa_inggris': 'medium'},
                'akuntansi': {'matematika': 'high', 'ekonomi': 'high'},
                'default': {'ekonomi': 'high', 'sejarah': 'medium', 'geografi': 'medium', 'sosiologi': 'medium', 'matematika': 'medium', 'bahasa_indonesia': 'medium', 'bahasa_inggris': 'basic'}
            }
        }
        
        program_mapping = major_mappings.get(program, {})
        
        # Find matching major category
        for category, subjects in program_mapping.items():
            if category == 'default':
                continue
            if category in major_name or any(keyword in major_name for keyword in category.split()):
                return subjects
        
        return program_mapping.get('default', {})
    
    def _filter_topics_for_major(self, subject: str, all_topics: List[str], major_name: str) -> List[str]:
        """Filter and prioritize topics based on major requirements"""
        # Major-specific topic prioritization
        if subject == 'matematika':
            if 'teknik' in major_name or 'informatika' in major_name:
                priority_topics = ['Fungsi, Komposisi, dan Invers', 'Limit Fungsi', 'Turunan dan Aplikasinya', 
                                 'Integral dan Aplikasinya', 'Trigonometri', 'Vektor']
            elif 'ekonomi' in major_name:
                priority_topics = ['Sistem Persamaan Linear', 'Program Linear', 'Statistika dan Peluang', 
                                 'Barisan dan Deret', 'Matematika Keuangan']
            else:
                priority_topics = all_topics[:8]
        elif subject == 'fisika' and ('teknik' in major_name or 'informatika' in major_name):
            priority_topics = ['Kinematika Gerak', 'Dinamika Partikel', 'Usaha dan Energi', 
                             'Listrik Statis', 'Listrik Dinamis', 'Kemagnetan']
        elif subject == 'biologi' and 'kedokteran' in major_name:
            priority_topics = ['Sel sebagai Unit Kehidupan', 'Sistem Organ pada Manusia', 
                             'Genetika', 'Biomolekul', 'Reproduksi dan Perkembangan']
        else:
            priority_topics = all_topics[:6]
        
        # Ensure we don't exceed available topics
        return priority_topics[:min(len(priority_topics), len(all_topics))]
    
    def process_message(self, message: str) -> ChatbotResponse:
        """Main method to process user message"""
        intent = self.detect_intent(message)
        
        if intent == 'grade_to_major':
            return self._handle_grade_to_major(message)
        elif intent == 'major_preparation':
            return self._handle_major_preparation(message)
        elif intent == 'study_tips':
            return self._handle_study_tips(message)
        elif intent == 'major_info':
            return self._handle_major_info(message)
        else:
            return self._handle_general(message)
    
    def _handle_grade_to_major(self, message: str) -> ChatbotResponse:
        """Handle grade-based major recommendation with detailed analysis"""
        grades = self.extract_grades_from_text(message)
        
        if not grades:
            return ChatbotResponse(
                message="""📊 **Untuk memberikan rekomendasi jurusan yang akurat, saya perlu informasi nilai rapor Anda.**

Contoh format yang bisa Anda gunakan:
• "Nilai matematika 85, fisika 80, kimia 78, rata-rata 82"
• "Rapor saya: matematika 90, biologi 88, kimia 85"
• "Nilai rata-rata rapor saya 85, matematika 88, fisika 82"

Sertakan juga nilai mata pelajaran yang relevan dengan minat Anda! 🎯""",
                recommendations=[],
                study_plan=[],
                confidence=0.3
            )
        
        # Determine program based on mentioned subjects
        program = self._determine_program_from_grades(grades)
        recommendations = self.recommend_majors_by_grades(grades, program)
        
        avg_grade = grades.get('rata_rata', sum(grades.values()) / len(grades))
        
        # Categorize recommendations
        very_likely = [r for r in recommendations if r['probability'] > 0.8]
        likely = [r for r in recommendations if 0.6 <= r['probability'] <= 0.8]
        possible = [r for r in recommendations if 0.4 <= r['probability'] < 0.6]
        
        # Generate personalized guidance
        guidance = self._generate_personalized_guidance(grades, avg_grade, very_likely, likely, possible)
        
        message = f"""📊 **Analisis Nilai Rapor Anda (Rata-rata: {avg_grade:.1f})**

{self._format_grade_breakdown(grades)}

🎯 **REKOMENDASI JURUSAN:**

🟢 **PELUANG BESAR (>80%)** - Sangat Direkomendasikan:
{self._format_major_list(very_likely, show_details=True)}

🟡 **PELUANG SEDANG (60-80%)** - Layak Dipertimbangkan:
{self._format_major_list(likely, show_details=True)}

🟠 **PELUANG KECIL (40-60%)** - Perlu Usaha Ekstra:
{self._format_major_list(possible, show_details=True)}

💡 **PANDUAN PERSONAL:**
{guidance}

🤔 **Masih bingung memilih?** Ceritakan minat dan cita-cita Anda, saya akan membantu mengarahkan pilihan yang tepat!"""
        
        return ChatbotResponse(
            message=message,
            recommendations=recommendations,
            study_plan=[],
            confidence=0.95
        )
    
    def _handle_major_preparation(self, message: str) -> ChatbotResponse:
        """Handle major preparation requests with comprehensive guidance"""
        # Extract major and university name from message
        major_keywords = self._extract_major_from_text(message)
        university_name = self._extract_university_from_text(message)
        
        if not major_keywords:
            return ChatbotResponse(
                message="""🤔 **Untuk memberikan panduan yang tepat, mohon sebutkan jurusan yang Anda targetkan.**

Contoh:
• "Saya ingin masuk Teknik Informatika"
• "Target saya Kedokteran di UI"
• "Mau ke jurusan Ekonomi ITB"

Atau jika masih bingung memilih jurusan, coba ceritakan:
• Mata pelajaran favorit Anda
• Bidang yang Anda minati
• Cita-cita karir Anda""",
                recommendations=[],
                study_plan=[],
                confidence=0.3
            )
        
        # Determine program
        program = self._determine_program_from_major(major_keywords)
        study_plan = self.get_study_plan_for_major(major_keywords, program)
        
        # Get specific recommendations for the major
        major_tips = self._get_major_specific_tips(major_keywords, university_name)
        
        # Find related majors in KB for additional context
        related_majors = self._find_related_majors(major_keywords, university_name)
        
        message = f"""🎯 **Panduan Persiapan untuk {major_keywords.title()}**
{f"di {university_name}" if university_name else ""}

📚 **Mata Pelajaran yang Harus Dikuasai:**

{self._format_study_plan(study_plan)}

💡 **Tips Khusus untuk {major_keywords.title()}:**
{major_tips}

📊 **Informasi Tambahan:**
{self._format_related_majors_info(related_majors)}

🎯 **Strategi Persiapan:**
1. **Fokus Utama**: Kuasai mata pelajaran inti dengan baik
2. **Latihan Rutin**: Kerjakan soal-soal UTBK 3-5 tahun terakhir
3. **Target Nilai**: Usahakan nilai rapor minimal 85 untuk mata pelajaran inti
4. **Pengalaman**: Ikuti olimpiade/kompetisi yang relevan jika memungkinkan
5. **Backup Plan**: Siapkan 2-3 pilihan jurusan alternatif

💪 **Jangan lupa untuk konsisten belajar dan tetap semangat!**"""
        
        return ChatbotResponse(
            message=message,
            recommendations=related_majors,
            study_plan=study_plan,
            confidence=0.9
        )
    
    def _handle_study_tips(self, message: str) -> ChatbotResponse:
        """Handle study tips requests"""
        message = """📚 **Tips Belajar Efektif untuk UTBK**

🎯 **Strategi Umum**:
• Buat jadwal belajar harian yang konsisten
• Gunakan teknik Pomodoro (25 menit fokus, 5 menit istirahat)
• Belajar dari buku referensi dan soal-soal UTBK terbaru
• Bergabung dengan grup belajar atau komunitas online

📖 **Per Mata Pelajaran**:
• **Matematika**: Pahami konsep dasar, latihan soal bertahap dari mudah ke sulit
• **Fisika**: Kuasai rumus, pahami konsep, banyak latihan soal cerita
• **Kimia**: Hafal tabel periodik, pahami reaksi kimia, latihan stoikiometri
• **Biologi**: Buat mind map, hafal istilah penting, pahami proses biologis

⏰ **Manajemen Waktu**:
• Alokasikan waktu lebih banyak untuk mata pelajaran yang lemah
• Sisakan waktu untuk review dan latihan soal campuran
• Jangan lupa istirahat dan menjaga kesehatan

🎯 **Target Harian**: Minimal 3-4 jam belajar efektif per hari"""
        
        return ChatbotResponse(
            message=message,
            recommendations=[],
            study_plan=[],
            confidence=0.7
        )
    
    def _handle_major_info(self, message: str) -> ChatbotResponse:
        """Handle major information requests"""
        major_name = self._extract_major_from_text(message)
        
        if not major_name:
            return ChatbotResponse(
                message="Jurusan mana yang ingin Anda ketahui informasinya?",
                recommendations=[],
                study_plan=[],
                confidence=0.3
            )
        
        # Find major info in KB
        matching_majors = []
        for key, data in self.majors_kb.items():
            if major_name.lower() in data.get('major', '').lower():
                matching_majors.append(data)
        
        if not matching_majors:
            return ChatbotResponse(
                message=f"Maaf, saya tidak menemukan informasi untuk jurusan {major_name}. Coba gunakan nama yang lebih spesifik.",
                recommendations=[],
                study_plan=[],
                confidence=0.2
            )
        
        # Get top 5 matches
        info_text = f"📋 **Informasi Jurusan {major_name.title()}**:\n\n"
        
        for i, major in enumerate(matching_majors[:5], 1):
            info_text += f"""**{i}. {major.get('university')} - {major.get('major')}**
   • Passing Grade: {major.get('passing_grade', 'N/A')}
   • Rata-rata Rapor: {major.get('required_rapor', 'N/A')}
   • Tingkat Persaingan: {major.get('competitiveness', 'N/A')}
   • Daya Tampung: {major.get('capacity', 'N/A')} orang
   • Acceptance Rate: {major.get('acceptance_rate', 'N/A')}%

"""
        
        return ChatbotResponse(
            message=info_text,
            recommendations=matching_majors[:5],
            study_plan=[],
            confidence=0.8
        )
    
    def _handle_general(self, message: str) -> ChatbotResponse:
        """Handle general queries"""
        message = """👋 **Halo! Saya chatbot konsultasi pendidikan**

Saya bisa membantu Anda dengan:

🎯 **Rekomendasi Jurusan** berdasarkan nilai rapor
Contoh: "Nilai matematika 85, fisika 80, kimia 78, rata-rata 82"

📚 **Rencana Belajar** untuk jurusan target
Contoh: "Saya ingin masuk Teknik Informatika"

💡 **Tips Belajar** untuk persiapan UTBK
Contoh: "Bagaimana cara belajar matematika yang efektif?"

📊 **Informasi Jurusan** dan passing grade
Contoh: "Info tentang jurusan Kedokteran"

Silakan tanyakan apa yang ingin Anda ketahui! 😊"""
        
        return ChatbotResponse(
            message=message,
            recommendations=[],
            study_plan=[],
            confidence=0.6
        )
    
    def _extract_major_from_text(self, text: str) -> str:
        """Extract major name from text"""
        text_lower = text.lower()
        
        # Common major keywords with more variations
        major_keywords = [
            'teknik informatika', 'informatika', 'kedokteran', 'farmasi', 'hukum',
            'ekonomi', 'manajemen', 'akuntansi', 'psikologi', 'komunikasi',
            'teknik sipil', 'teknik mesin', 'teknik elektro', 'arsitektur',
            'biologi', 'kimia', 'fisika', 'matematika', 'sastra inggris',
            'hubungan internasional', 'administrasi', 'keperawatan',
            'teknik industri', 'sistem informasi', 'ilmu komputer',
            'desain grafis', 'broadcasting', 'jurnalistik', 'perpustakaan',
            'gizi', 'kesehatan masyarakat', 'kebidanan', 'fisioterapi'
        ]
        
        # Sort by length (longer first) to match more specific terms first
        major_keywords.sort(key=len, reverse=True)
        
        for keyword in major_keywords:
            if keyword in text_lower:
                return keyword
        
        return ""
    
    def _determine_program_from_major(self, major_name: str) -> str:
        """Determine program (saintek/soshum) from major name"""
        saintek_keywords = ['teknik', 'informatika', 'kedokteran', 'farmasi', 'biologi', 
                           'kimia', 'fisika', 'matematika', 'arsitektur', 'gizi', 
                           'kesehatan', 'kebidanan', 'fisioterapi', 'sistem informasi', 
                           'ilmu komputer']
        
        if any(keyword in major_name.lower() for keyword in saintek_keywords):
            return 'saintek'
        else:
            return 'soshum'
    
    def _format_major_list(self, majors: List[Dict], show_details: bool = False) -> str:
        """Format major list for display"""
        if not majors:
            return "• Tidak ada jurusan dalam kategori ini\n"
        
        result = ""
        for major in majors[:5]:  # Limit to 5 per category
            if show_details:
                result += f"• **{major['major']}** ({major['university']}) - Peluang: {major['probability']*100:.1f}%\n"
                if major.get('required_rapor'):
                    result += f"  - Rata-rata Rapor Required: {major['required_rapor']}\n"
                if major.get('current_gap'):
                    gap = major['current_gap']
                    if gap > 0:
                        result += f"  - Gap: +{gap:.1f} (Anda sudah melampaui requirement)\n"
                    else:
                        result += f"  - Gap: {gap:.1f} (Perlu ditingkatkan)\n"
            else:
                result += f"• **{major['major']}** ({major['university']}) - Peluang: {major['probability']*100:.1f}%\n"
        
        return result
    
    def _format_study_plan(self, study_plan: List[SubjectTopic]) -> str:
        """Format study plan for display"""
        result = ""
        
        for i, subject_plan in enumerate(study_plan, 1):
            difficulty_emoji = '🔥' if subject_plan.difficulty == 'advanced' else '📋' if subject_plan.difficulty == 'intermediate' else '📝'
            
            result += f"""
**{i}. {subject_plan.subject.replace('_', ' ').title()}** {difficulty_emoji}
Topik yang harus dikuasai:"""
            
            for j, topic in enumerate(subject_plan.topics, 1):
                result += f"\n   {j}. {topic}"
            
            result += "\n"
        
        return result
    
    def _get_major_specific_tips(self, major_name: str, university_name: str = None) -> str:
        """Get major-specific tips and requirements"""
        major_lower = major_name.lower()
        tips = []
        
        if 'informatika' in major_lower or 'komputer' in major_lower:
            tips = [
                "• **Matematika** adalah fondasi utama - kuasai logika, aljabar, dan statistika",
                "• **Algoritma & Pemrograman** - mulai belajar bahasa pemrograman seperti Python/Java",
                "• **Logika Berpikir** - latihan soal-soal logika dan problem solving",
                "• **Bahasa Inggris** - penting untuk membaca dokumentasi teknis",
                "• **Portofolio** - buat project sederhana untuk menunjukkan kemampuan"
            ]
        elif 'kedokteran' in major_lower:
            tips = [
                "• **Biologi** - fokus pada anatomi, fisiologi, dan biokimia",
                "• **Kimia** - kuasai kimia organik dan biokimia",
                "• **Fisika** - pahami prinsip fisika dalam tubuh manusia",
                "• **Bahasa Inggris** - untuk membaca jurnal medis internasional",
                "• **Soft Skills** - empati, komunikasi, dan ketahanan mental"
            ]
        elif 'teknik' in major_lower:
            tips = [
                "• **Matematika & Fisika** - dasar semua cabang teknik",
                "• **Problem Solving** - latihan soal-soal aplikatif",
                "• **Kreativitas** - kemampuan berpikir inovatif",
                "• **Kerja Tim** - banyak project berbasis kelompok",
                "• **Update Teknologi** - ikuti perkembangan teknologi terkini"
            ]
        elif 'ekonomi' in major_lower or 'manajemen' in major_lower:
            tips = [
                "• **Matematika** - statistika, kalkulus, dan matematika bisnis",
                "• **Bahasa Inggris** - komunikasi bisnis internasional",
                "• **Analisis** - kemampuan berpikir kritis dan analitis",
                "• **Leadership** - keterampilan kepemimpinan dan manajemen",
                "• **Current Issues** - ikuti perkembangan ekonomi dan bisnis"
            ]
        elif 'hukum' in major_lower:
            tips = [
                "• **Bahasa Indonesia** - kemampuan menulis dan berargumentasi",
                "• **Sejarah** - memahami sejarah hukum dan konstitusi",
                "• **Logika** - kemampuan berpikir sistematis dan analitis",
                "• **Public Speaking** - keterampilan berbicara di depan umum",
                "• **Reading** - banyak membaca kasus hukum dan perundangan"
            ]
        else:
            tips = [
                "• **Mata Pelajaran Inti** - fokus pada mapel yang relevan dengan jurusan",
                "• **Soft Skills** - komunikasi, leadership, dan teamwork",
                "• **Wawasan Umum** - perbanyak membaca dan update informasi",
                "• **Pengalaman** - ikuti kegiatan ekstrakurikuler yang relevan",
                "• **Networking** - bangun relasi dengan senior di bidang yang sama"
            ]
        
        return "\n".join(tips)
    
    def _find_related_majors(self, major_name: str, university_name: str = None) -> List[Dict]:
        """Find related majors in the knowledge base"""
        related = []
        major_lower = major_name.lower()
        
        for key, major_data in self.majors_kb.items():
            if not major_data.get('university') or not major_data.get('major'):
                continue
                
            kb_major = major_data.get('major', '').lower()
            kb_university = major_data.get('university', '').lower()
            
            # Check if major matches
            is_major_match = any(word in kb_major for word in major_lower.split())
            
            # Check university match if specified
            is_university_match = True
            if university_name:
                uni_lower = university_name.lower()
                is_university_match = uni_lower in kb_university or any(
                    alias.lower() in kb_university for alias, full in self.university_aliases.items() 
                    if full.lower() == uni_lower
                )
            
            if is_major_match and is_university_match:
                related.append({
                    'university': major_data.get('university'),
                    'major': major_data.get('major'),
                    'required_rapor': major_data.get('required_rapor'),
                    'passing_grade': major_data.get('passing_grade'),
                    'acceptance_rate': major_data.get('acceptance_rate'),
                    'competitiveness': major_data.get('competitiveness')
                })
        
        # Sort by acceptance rate (higher is better) and required rapor (lower is better)
        related.sort(key=lambda x: (
            -(x.get('acceptance_rate') or 0),
            x.get('required_rapor') or 100
        ))
        
        return related[:5]  # Return top 5
    
    def _format_related_majors_info(self, related_majors: List[Dict]) -> str:
        """Format related majors information"""
        if not related_majors:
            return "• Informasi detail tidak tersedia dalam database"
        
        result = ""
        for i, major in enumerate(related_majors, 1):
            result += f"""
**{i}. {major['major']} - {major['university']}**
   • Rata-rata Rapor: {major.get('required_rapor', 'N/A')}
   • Passing Grade: {major.get('passing_grade', 'N/A')}
   • Acceptance Rate: {major.get('acceptance_rate', 'N/A')}%
   • Tingkat Persaingan: {major.get('competitiveness', 'N/A')}"""
        
        return result
    
    def _format_grade_breakdown(self, grades: Dict[str, float]) -> str:
        """Format grade breakdown for display"""
        result = "**Nilai yang Anda berikan:**\n"
        
        for subject, grade in grades.items():
            if subject != 'rata_rata':
                subject_display = subject.replace('_', ' ').title()
                result += f"• {subject_display}: {grade}\n"
        
        return result
    
    def _generate_personalized_guidance(self, grades: Dict[str, float], avg_grade: float, 
                                      very_likely: List[Dict], likely: List[Dict], 
                                      possible: List[Dict]) -> str:
        """Generate personalized guidance based on grades and recommendations"""
        guidance = []
        
        # Analyze grade pattern
        if avg_grade >= 90:
            guidance.append("🌟 Nilai Anda sangat excellent! Hampir semua jurusan terbuka untuk Anda.")
        elif avg_grade >= 85:
            guidance.append("👍 Nilai Anda sangat baik! Banyak pilihan jurusan berkualitas menanti.")
        elif avg_grade >= 80:
            guidance.append("✅ Nilai Anda cukup baik! Fokus pada jurusan yang sesuai minat.")
        elif avg_grade >= 75:
            guidance.append("💪 Masih ada peluang bagus! Tingkatkan nilai di semester terakhir.")
        else:
            guidance.append("🎯 Fokus perbaiki nilai semester terakhir untuk membuka lebih banyak peluang.")
        
        # Subject-specific advice
        if 'matematika' in grades and grades['matematika'] >= 85:
            guidance.append("• Nilai matematika Anda bagus - cocok untuk jurusan Saintek/Ekonomi")
        if 'fisika' in grades and grades['fisika'] >= 85:
            guidance.append("• Nilai fisika tinggi - pertimbangkan jurusan Teknik")
        if 'biologi' in grades and grades['biologi'] >= 85:
            guidance.append("• Nilai biologi excellent - Kedokteran/Farmasi bisa jadi pilihan")
        if 'bahasa_indonesia' in grades and grades['bahasa_indonesia'] >= 85:
            guidance.append("• Kemampuan bahasa baik - cocok untuk jurusan Soshum")
        
        # Recommendation-based advice
        if len(very_likely) >= 3:
            guidance.append("• Anda memiliki banyak pilihan dengan peluang tinggi - pilih yang sesuai minat")
        elif len(very_likely) == 0 and len(likely) > 0:
            guidance.append("• Fokus pada pilihan dengan peluang sedang dan siapkan backup plan")
        elif len(very_likely) == 0 and len(likely) == 0:
            guidance.append("• Tingkatkan nilai secara signifikan atau pertimbangkan target yang lebih realistis")
        
        return "\n".join(guidance)