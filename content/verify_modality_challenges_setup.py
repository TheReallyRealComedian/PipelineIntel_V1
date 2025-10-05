#!/usr/bin/env python3
"""
Verification script for Modality Challenge Inheritance setup.
Run this AFTER making all code changes to verify everything is configured correctly.

Usage: python verify_modality_challenges_setup.py
"""

def verify_setup():
    """Check if all components are properly configured."""
    
    print("=" * 70)
    print("MODALITY CHALLENGE INHERITANCE - SETUP VERIFICATION")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    success = []
    
    # Check 1: Import ModalityChallenge model
    print("✓ Checking Model Import...")
    try:
        from backend.models import ModalityChallenge
        success.append("✅ ModalityChallenge model can be imported")
    except ImportError as e:
        errors.append(f"❌ Cannot import ModalityChallenge model: {e}")
    
    # Check 2: Verify model attributes
    print("✓ Checking Model Attributes...")
    try:
        from backend.models import ModalityChallenge
        required_attrs = ['modality_id', 'challenge_id', 'is_typical', 'notes', 'created_at']
        for attr in required_attrs:
            if not hasattr(ModalityChallenge, attr):
                errors.append(f"❌ ModalityChallenge missing attribute: {attr}")
        if not errors:
            success.append("✅ ModalityChallenge has all required attributes")
    except Exception as e:
        errors.append(f"❌ Error checking ModalityChallenge attributes: {e}")
    
    # Check 3: Verify Modality relationship
    print("✓ Checking Modality Relationships...")
    try:
        from backend.models import Modality
        if hasattr(Modality, 'modality_challenges'):
            success.append("✅ Modality has modality_challenges relationship")
        else:
            errors.append("❌ Modality missing modality_challenges relationship")
    except Exception as e:
        errors.append(f"❌ Error checking Modality: {e}")
    
    # Check 4: Verify ManufacturingChallenge relationship
    print("✓ Checking ManufacturingChallenge Relationships...")
    try:
        from backend.models import ManufacturingChallenge
        if hasattr(ManufacturingChallenge, 'modality_links'):
            success.append("✅ ManufacturingChallenge has modality_links relationship")
        else:
            errors.append("❌ ManufacturingChallenge missing modality_links relationship")
    except Exception as e:
        errors.append(f"❌ Error checking ManufacturingChallenge: {e}")
    
    # Check 5: Verify Product.get_inherited_challenges method
    print("✓ Checking Product Methods...")
    try:
        from backend.models import Product
        if hasattr(Product, 'get_inherited_challenges'):
            success.append("✅ Product has get_inherited_challenges() method")
            # Check if it includes modality logic
            import inspect
            source = inspect.getsource(Product.get_inherited_challenges)
            if 'modality.modality_challenges' in source:
                success.append("✅ get_inherited_challenges() includes modality logic")
            else:
                warnings.append("⚠️ get_inherited_challenges() may not include modality logic")
        else:
            errors.append("❌ Product missing get_inherited_challenges() method")
    except Exception as e:
        errors.append(f"❌ Error checking Product: {e}")
    
    # Check 6: Verify import service configuration
    print("✓ Checking Import Service Configuration...")
    try:
        from backend.services.data_management_service import MODEL_MAP, TABLE_IMPORT_ORDER
        if 'modality_challenges' in MODEL_MAP:
            success.append("✅ modality_challenges in MODEL_MAP")
        else:
            errors.append("❌ modality_challenges NOT in MODEL_MAP")
        
        if 'modality_challenges' in TABLE_IMPORT_ORDER:
            success.append("✅ modality_challenges in TABLE_IMPORT_ORDER")
            # Check order - should come after modalities and manufacturing_challenges
            mc_idx = TABLE_IMPORT_ORDER.index('modality_challenges')
            mod_idx = TABLE_IMPORT_ORDER.index('modalities')
            chal_idx = TABLE_IMPORT_ORDER.index('manufacturing_challenges')
            if mc_idx > mod_idx and mc_idx > chal_idx:
                success.append("✅ modality_challenges is in correct import order")
            else:
                errors.append("❌ modality_challenges is in wrong position in TABLE_IMPORT_ORDER (must come AFTER modalities and manufacturing_challenges)")
        else:
            errors.append("❌ modality_challenges NOT in TABLE_IMPORT_ORDER")
    except Exception as e:
        errors.append(f"❌ Error checking import service: {e}")
    
    # Check 7: Verify database table exists
    print("✓ Checking Database Table...")
    try:
        from backend.db import db
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'modality_challenges' in inspector.get_table_names():
            success.append("✅ modality_challenges table exists in database")
        else:
            warnings.append("⚠️ modality_challenges table does NOT exist (run migration: flask db upgrade)")
    except Exception as e:
        warnings.append(f"⚠️ Cannot check database: {e}")
    
    # Print results
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    if success:
        print("✅ SUCCESSFUL CHECKS:")
        for item in success:
            print(f"   {item}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for item in warnings:
            print(f"   {item}")
        print()
    
    if errors:
        print("❌ ERRORS (MUST FIX):")
        for item in errors:
            print(f"   {item}")
        print()
    
    # Overall status
    print("=" * 70)
    if errors:
        print("❌ SETUP INCOMPLETE - Fix errors above before proceeding")
        return False
    elif warnings:
        print("⚠️  SETUP MOSTLY COMPLETE - Review warnings")
        print("   You can proceed with JSON transformation, but run migration first")
        return True
    else:
        print("✅ SETUP COMPLETE - Ready to transform JSON files!")
        return True
    print("=" * 70)


if __name__ == "__main__":
    try:
        verify_setup()
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()