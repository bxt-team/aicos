#!/usr/bin/env python3
"""
Test script für die optimierte 7 Cycles Affirmations-Generierung
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_7cycles_periods():
    """Test die 7 Cycles Perioden"""
    try:
        from app.agents.affirmations_agent import AffirmationsAgent
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("✗ OPENAI_API_KEY nicht gefunden")
            return False
        
        print("🧪 Teste 7 Cycles Affirmations-Generierung")
        print("=" * 50)
        
        agent = AffirmationsAgent(openai_api_key)
        
        # Test verfügbare Perioden
        periods = agent.get_available_periods()
        print(f"✓ Verfügbare 7 Cycles Perioden: {len(periods['period_types'])}")
        
        for period_name, details in periods['period_types'].items():
            print(f"  📍 {period_name} ({details['color']})")
            print(f"     {details['description']}")
            print(f"     Fokus: {details['focus']}")
            print()
        
        # Test Affirmations-Generierung für jede Periode
        test_periods = ["Image", "Energie", "Kreativität"]
        
        for period_name in test_periods:
            print(f"🎯 Teste Affirmationen für: {period_name}")
            
            result = agent.generate_affirmations(
                period_name=period_name,
                period_info={"test": True},
                count=3
            )
            
            if result["success"]:
                print(f"✓ {len(result['affirmations'])} Affirmationen generiert")
                
                for i, affirmation in enumerate(result['affirmations'], 1):
                    print(f"  {i}. \"{affirmation['text']}\"")
                    print(f"     Theme: {affirmation['theme']}")
                    print(f"     Fokus: {affirmation['focus']}")
                    print(f"     Farbe: {affirmation.get('period_color', 'N/A')}")
                    print()
            else:
                print(f"✗ Fehler bei {period_name}: {result['error']}")
                return False
        
        print("🎉 Alle Tests erfolgreich!")
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_period_validation():
    """Test die Validierung der Perioden-Namen"""
    try:
        from app.agents.affirmations_agent import AffirmationsAgent
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return False
        
        print("🔍 Teste Perioden-Validierung")
        print("-" * 30)
        
        agent = AffirmationsAgent(openai_api_key)
        
        # Test ungültige Periode
        result = agent.generate_affirmations(
            period_name="UngültigePeriode",
            period_info={},
            count=1
        )
        
        if not result["success"] and "Ungültige Periode" in result["error"]:
            print("✓ Validierung funktioniert korrekt")
            return True
        else:
            print("✗ Validierung fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"✗ Fehler bei Validierung: {e}")
        return False

def test_colors_integration():
    """Test die Farb-Integration"""
    try:
        from app.agents.affirmations_agent import AffirmationsAgent
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return False
        
        print("🎨 Teste Farb-Integration")
        print("-" * 25)
        
        agent = AffirmationsAgent(openai_api_key)
        
        expected_colors = {
            "Image": "#DAA520",
            "Veränderung": "#2196F3", 
            "Energie": "#F44336",
            "Kreativität": "#FFD700",
            "Erfolg": "#CC0066",
            "Entspannung": "#4CAF50",
            "Umsicht": "#9C27B0"
        }
        
        # Test eine Periode
        result = agent.generate_affirmations(
            period_name="Energie",
            period_info={},
            count=1
        )
        
        if result["success"]:
            affirmation = result['affirmations'][0]
            expected_color = expected_colors["Energie"]
            actual_color = affirmation.get('period_color')
            
            if actual_color == expected_color:
                print(f"✓ Farbe korrekt: {actual_color}")
                return True
            else:
                print(f"✗ Falsche Farbe: erwartet {expected_color}, erhalten {actual_color}")
                return False
        else:
            print(f"✗ Fehler beim Generieren: {result['error']}")
            return False
            
    except Exception as e:
        print(f"✗ Fehler bei Farb-Test: {e}")
        return False

def main():
    """Führe alle Tests aus"""
    print("🧪 7 Cycles Affirmations Optimierung - Tests")
    print("=" * 60)
    
    tests = [
        ("7 Cycles Perioden", test_7cycles_periods),
        ("Perioden-Validierung", test_period_validation),
        ("Farb-Integration", test_colors_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🏃 Teste: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - BESTANDEN")
        else:
            print(f"❌ {test_name} - FEHLGESCHLAGEN")
    
    print("\n" + "=" * 60)
    print(f"📊 Ergebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests erfolgreich! 7 Cycles Optimierung funktioniert korrekt.")
        return True
    else:
        print("❌ Einige Tests fehlgeschlagen. Bitte überprüfen.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)