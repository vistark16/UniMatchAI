"""
Prepare student data from dummy_data_SNDP_2025.xlsx for model training.
This script processes the Excel file and creates training data for the ML model.

Output: 
- data/processed_student_data.json (for model training)
- data/student_statistics.json (for feature distributions)
"""

import json
import pathlib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "dummy_data_SNDP_2025.xlsx"
OUT_DATA = ROOT / "data" / "processed_student_data.json"
OUT_STATS = ROOT / "data" / "student_statistics.json"

# Ensure output directory exists
OUT_DATA.parent.mkdir(parents=True, exist_ok=True)

def clean_text(text):
    """Clean and standardize text data"""
    if pd.isna(text) or text is None:
        return None
    return str(text).strip().upper()

def calculate_subject_averages(row):
    """Calculate various subject averages for a student"""
    # Subject mapping based on the Excel columns
    subjects = {
        'agama': row[0],
        'ppkn': row[1], 
        'bahasa_indonesia': row[2],
        'bahasa_inggris': row[3],
        'matematika_wajib': row[4],
        'seni_budaya': row[5],
        'pjok': row[6],
        'prakarya': row[7],
        'matematika_peminatan': row[8],
        'fisika': row[9],
        'kimia': row[10],
        'biologi': row[11],
        'geografi': row[12],
        'sejarah': row[13],
        'sosiologi': row[14],
        'ekonomi': row[15],
        'sastra_indonesia': row[16],
        'sastra_inggris': row[17],
        'bahasa_asing': row[18],
        'antropologi': row[19]
    }
    
    # Remove None values
    valid_subjects = {k: v for k, v in subjects.items() if pd.notna(v) and isinstance(v, (int, float))}
    
    # Calculate different averages
    averages = {}
    
    # Overall average (all subjects)
    if valid_subjects:
        averages['rapor_avg'] = np.mean(list(valid_subjects.values()))
    else:
        averages['rapor_avg'] = 0.0
        
    # Core subjects for all programs
    core_subjects = ['matematika_wajib', 'bahasa_indonesia', 'bahasa_inggris']
    core_values = [valid_subjects.get(subj) for subj in core_subjects if valid_subjects.get(subj)]
    averages['core_avg'] = np.mean(core_values) if core_values else averages['rapor_avg']
    
    # Program-specific averages
    program = clean_text(row[20])  # SMA Background column
    
    if program == 'IPA':
        # SAINTEK subjects
        saintek_subjects = ['matematika_wajib', 'matematika_peminatan', 'fisika', 'kimia', 'biologi', 'bahasa_indonesia', 'bahasa_inggris']
        saintek_values = [valid_subjects.get(subj) for subj in saintek_subjects if valid_subjects.get(subj)]
        averages['program_avg'] = np.mean(saintek_values) if saintek_values else averages['rapor_avg']
        
        # Individual subject grades for feature engineering
        averages['math'] = valid_subjects.get('matematika_peminatan') or valid_subjects.get('matematika_wajib', 0)
        averages['physics'] = valid_subjects.get('fisika', 0)
        averages['chemistry'] = valid_subjects.get('kimia', 0)
        averages['biology'] = valid_subjects.get('biologi', 0)
        averages['language'] = (valid_subjects.get('bahasa_indonesia', 0) + valid_subjects.get('bahasa_inggris', 0)) / 2
        
    elif program == 'IPS':
        # SOSHUM subjects  
        soshum_subjects = ['matematika_wajib', 'bahasa_indonesia', 'bahasa_inggris', 'geografi', 'sejarah', 'sosiologi', 'ekonomi']
        soshum_values = [valid_subjects.get(subj) for subj in soshum_subjects if valid_subjects.get(subj)]
        averages['program_avg'] = np.mean(soshum_values) if soshum_values else averages['rapor_avg']
        
        # Individual subject grades
        averages['math'] = valid_subjects.get('matematika_wajib', 0)
        averages['economics'] = valid_subjects.get('ekonomi', 0)
        averages['geography'] = valid_subjects.get('geografi', 0)
        averages['history'] = valid_subjects.get('sejarah', 0)
        averages['language'] = (valid_subjects.get('bahasa_indonesia', 0) + valid_subjects.get('bahasa_inggris', 0)) / 2
        
    else:
        averages['program_avg'] = averages['rapor_avg']
        averages['math'] = valid_subjects.get('matematika_wajib', 0)
        averages['language'] = (valid_subjects.get('bahasa_indonesia', 0) + valid_subjects.get('bahasa_inggris', 0)) / 2
    
    return averages, valid_subjects

def determine_program_compatibility(program, major, category):
    """Determine if program matches the major"""
    program = clean_text(program)
    major = clean_text(major)
    category = clean_text(category)
    
    # Simple heuristic based on category and common major patterns
    if category == 'SCIENTECH':
        return 1 if program == 'IPA' else 0
    elif category == 'SOSUM':
        # SOSUM can be both IPA and IPS depending on the major
        if any(keyword in major for keyword in ['TEKNIK', 'INFORMATIKA', 'KEDOKTERAN', 'FARMASI', 'BIOLOGI']):
            return 1 if program == 'IPA' else 0
        else:
            return 1 if program == 'IPS' else 0
    elif category == 'BAHASA':
        return 1 if program == 'IPS' else 0
    
    return 1  # Default: compatible

def create_training_features(student_data):
    """Create feature set for ML training"""
    features = {
        # Academic performance
        'rapor_avg': student_data['averages']['rapor_avg'],
        'core_avg': student_data['averages']['core_avg'],
        'program_avg': student_data['averages']['program_avg'],
        'math_score': student_data['averages']['math'],
        'language_score': student_data['averages']['language'],
        
        # Program type
        'program_saintek': 1 if student_data['program'] == 'IPA' else 0,
        'program_soshum': 1 if student_data['program'] == 'IPS' else 0,
        
        # Program compatibility (feature engineering)
        'program_match': student_data['program_match'],
        
        # Subject-specific scores (if available)
        'physics_score': student_data['averages'].get('physics', 0),
        'chemistry_score': student_data['averages'].get('chemistry', 0),
        'biology_score': student_data['averages'].get('biologi', 0),
        'economics_score': student_data['averages'].get('economics', 0),
        'geography_score': student_data['averages'].get('geography', 0),
        'history_score': student_data['averages'].get('history', 0),
    }
    
    # Target variable: acceptance (always 1 since these are accepted students)
    target = 1
    
    return features, target

def calculate_statistics(processed_data):
    """Calculate statistics for feature normalization"""
    stats = {}
    
    # Collect all features
    all_features = {}
    for item in processed_data:
        for key, value in item['features'].items():
            if key not in all_features:
                all_features[key] = []
            all_features[key].append(value)
    
    # Calculate statistics for each feature
    for feature, values in all_features.items():
        values = [v for v in values if v is not None and not np.isnan(v)]
        if values:
            stats[feature] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'median': float(np.median(values)),
                'count': len(values)
            }
    
    # University and major distributions
    universities = {}
    majors = {}
    categories = {}
    
    for item in processed_data:
        uni = item['university']
        maj = item['major']
        cat = item['category']
        
        universities[uni] = universities.get(uni, 0) + 1
        majors[maj] = majors.get(maj, 0) + 1
        categories[cat] = categories.get(cat, 0) + 1
    
    stats['distributions'] = {
        'universities': universities,
        'majors': majors,
        'categories': categories,
        'total_students': len(processed_data)
    }
    
    return stats

def main():
    print(f"Reading data from: {SRC}")
    
    # Read Excel file
    df = pd.read_excel(SRC)
    print(f"Loaded {len(df)} rows")
    
    # Define column names based on our analysis
    column_names = [
        'agama', 'ppkn', 'bahasa_indonesia', 'bahasa_inggris', 'matematika_wajib',
        'seni_budaya', 'pjok', 'prakarya', 'matematika_peminatan', 'fisika',
        'kimia', 'biologi', 'geografi', 'sejarah', 'sosiologi', 'ekonomi',
        'sastra_indonesia', 'sastra_inggris', 'bahasa_asing', 'antropologi',
        'program', 'major', 'university', 'category'
    ]
    
    # Assign proper column names
    df.columns = column_names[:len(df.columns)]
    
    processed_data = []
    skipped_rows = 0
    
    for idx, row in df.iterrows():
        # Skip rows without major/university info
        if pd.isna(row.get('major')) or pd.isna(row.get('university')):
            skipped_rows += 1
            continue
            
        # Calculate averages and extract features
        averages, valid_subjects = calculate_subject_averages(row.values)
        
        # Clean text fields
        program = clean_text(row.get('program'))
        major = clean_text(row.get('major'))
        university = clean_text(row.get('university'))
        category = clean_text(row.get('category'))
        
        # Determine program compatibility
        program_match = determine_program_compatibility(program, major, category)
        
        # Create student data object
        student_data = {
            'student_id': idx,
            'program': program,
            'major': major,
            'university': university, 
            'category': category,
            'averages': averages,
            'valid_subjects': valid_subjects,
            'program_match': program_match
        }
        
        # Create ML features
        features, target = create_training_features(student_data)
        
        processed_item = {
            **student_data,
            'features': features,
            'target': target
        }
        
        processed_data.append(processed_item)
    
    print(f"Processed {len(processed_data)} students")
    print(f"Skipped {skipped_rows} rows due to missing data")
    
    # Calculate statistics
    print("Calculating statistics...")
    statistics = calculate_statistics(processed_data)
    
    # Save processed data
    print(f"Saving processed data to: {OUT_DATA}")
    with open(OUT_DATA, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    # Save statistics
    print(f"Saving statistics to: {OUT_STATS}")
    with open(OUT_STATS, 'w', encoding='utf-8') as f:
        json.dump(statistics, f, ensure_ascii=False, indent=2)
    
    # Print summary statistics
    print("\n=== SUMMARY ===")
    print(f"Total students processed: {len(processed_data)}")
    print(f"Average rapor score: {statistics['rapor_avg']['mean']:.2f}")
    print(f"Universities: {len(statistics['distributions']['universities'])}")
    print(f"Majors: {len(statistics['distributions']['majors'])}")
    print(f"Categories: {len(statistics['distributions']['categories'])}")
    
    print("\nTop 10 universities:")
    top_unis = sorted(statistics['distributions']['universities'].items(), 
                     key=lambda x: x[1], reverse=True)[:10]
    for uni, count in top_unis:
        print(f"  {uni}: {count} students")
    
    print("\nTop 10 majors:")
    top_majors = sorted(statistics['distributions']['majors'].items(), 
                       key=lambda x: x[1], reverse=True)[:10]
    for major, count in top_majors:
        print(f"  {major}: {count} students")

if __name__ == "__main__":
    main()