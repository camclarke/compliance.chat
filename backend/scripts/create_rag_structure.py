import os
import argparse

# The ISO 17000 functional definition structure provided by the user
DIRECTORY_STRUCTURE = {
    "01_specified_requirements": [
        "electrical_safety",
        "radio_and_telecom",
        "energy_efficiency",
        "labeling_and_product_info",
        "medical_devices",
        "textile_and_apparel",
        "environmental_protection"
    ],
    "02_conformity_assessment_bodies": [
        "testing_laboratories",
        "certification_bodies",
        "inspection_bodies",
        "mutual_recognition_agreements"
    ],
    "03_conformity_assessment_schemes": [
        "general_procedures",
        "electrical_safety",
        "radio_and_telecom",
        "energy_efficiency",
        "medical_devices",
        "textile_and_apparel",
        "environmental_protection"
    ],
    "04_applicability_references": [
        "hs_code_correlation_tables",
        "exemption_criteria",
        "product_classification_guides",
        "equivalency_tables",
        "prohibited_and_restricted_lists"
    ]
}

def create_country_structure(base_path: str, iso_codes: list[str]):
    """
    Creates the definitive universal compliance folder structure for the specified ISO alpha-3 codes.
    Uses strictly lower-case for Azure Blob compatibility.
    """
    for iso_code in iso_codes:
        iso_code = iso_code.lower()
        print(f"Generating folder structure for: {iso_code}")
        
        country_path = os.path.join(base_path, iso_code)
        
        for parent_dir, sub_dirs in DIRECTORY_STRUCTURE.items():
            parent_path = os.path.join(country_path, parent_dir)
            os.makedirs(parent_path, exist_ok=True)
            
            for sub_dir in sub_dirs:
                sub_path = os.path.join(parent_path, sub_dir)
                os.makedirs(sub_path, exist_ok=True)
                
                # Create a simple .gitkeep to ensure empty folders are tracked if pushed to git
                with open(os.path.join(sub_path, ".gitkeep"), "w") as f:
                    pass

    print(f"\n✅ Successfully created universal compliance structure at: {os.path.abspath(base_path)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate RAG Document Folder Structure")
    parser.add_argument(
        "--countries", 
        nargs="+", 
        default=["mex", "usa", "pan", "bra", "gbr"],
        help="List of ISO Alpha-3 country codes (e.g., mex usa bra)"
    )
    parser.add_argument(
        "--base-dir", 
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "compliance-library", "countries"),
        help="Base directory path"
    )
    
    args = parser.parse_args()
    create_country_structure(args.base_dir, args.countries)
