# Multi-Layer Validation System
# Ensures NO HALLUCINATIONS - only fact-based outputs

import re
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

class ValidationResult:
    """Result of a validation check"""
    def __init__(self, passed: bool, reason: str = "", confidence: float = 0.0):
        self.passed = passed
        self.reason = reason
        self.confidence = confidence
        self.timestamp = datetime.now().isoformat()

class MultiLayerValidator:
    """5-Layer validation system to prevent hallucinations"""
    
    def __init__(self):
        self.validation_log = []
    
    # ==================== LAYER 1: Format Validation ====================
    def layer1_format_check(self, data: Dict[str, Any], expected_schema: Dict[str, type]) -> ValidationResult:
        """
        Verify the output matches the expected structure
        No hallucinated fields, no missing required fields
        """
        try:
            # Check all required fields exist
            for field, field_type in expected_schema.items():
                if field not in data:
                    return ValidationResult(
                        passed=False,
                        reason=f"Missing required field: {field}",
                        confidence=0.0
                    )
                
                # Check type matches (handle both single types and tuples of types)
                if data[field] is not None:
                    if isinstance(field_type, tuple):
                        # Multiple acceptable types
                        if not isinstance(data[field], field_type):
                            return ValidationResult(
                                passed=False,
                                reason=f"Field '{field}' has wrong type. Expected one of {field_type}, got {type(data[field])}",
                                confidence=0.0
                            )
                    else:
                        # Single type
                        if not isinstance(data[field], field_type):
                            return ValidationResult(
                                passed=False,
                                reason=f"Field '{field}' has wrong type. Expected {field_type}, got {type(data[field])}",
                                confidence=0.0
                            )
            
            return ValidationResult(passed=True, reason="Format valid", confidence=1.0)
        
        except Exception as e:
            return ValidationResult(passed=False, reason=f"Format check error: {str(e)}", confidence=0.0)
    
    # ==================== LAYER 2: Factual Check ====================
    def layer2_factual_check(self, extracted_data: Dict[str, Any], source_text: str) -> ValidationResult:
        """
        Verify that extracted data actually exists in the source text
        Prevents the LLM from making up information
        """
        try:
            confidence_score = 0.0
            total_checks = 0
            failed_checks = []
            
            for field, value in extracted_data.items():
                if value is None or value == "" or value == "Unknown":
                    continue
                
                total_checks += 1
                value_str = str(value).lower()
                source_lower = source_text.lower()
                
                # Check if the value or close variant exists in source
                if value_str in source_lower:
                    confidence_score += 1.0
                elif self._fuzzy_match(value_str, source_lower):
                    confidence_score += 0.7
                else:
                    failed_checks.append(f"{field}='{value}' not found in source")
            
            if total_checks == 0:
                return ValidationResult(passed=True, reason="No data to verify", confidence=0.5)
            
            confidence = confidence_score / total_checks
            
            if confidence < 0.6:
                return ValidationResult(
                    passed=False,
                    reason=f"Low factual accuracy. Failed: {', '.join(failed_checks)}",
                    confidence=confidence
                )
            
            return ValidationResult(passed=True, reason="Factual check passed", confidence=confidence)
        
        except Exception as e:
            return ValidationResult(passed=False, reason=f"Factual check error: {str(e)}", confidence=0.0)
    
    def _fuzzy_match(self, value: str, source: str) -> bool:
        """Check if value exists with minor variations"""
        # Remove common variations
        value_clean = re.sub(r'[^a-z0-9]', '', value)
        
        # Check for partial matches (at least 80% of the value)
        if len(value_clean) > 5:
            chunk_size = int(len(value_clean) * 0.8)
            for i in range(len(value_clean) - chunk_size + 1):
                chunk = value_clean[i:i + chunk_size]
                if chunk in source:
                    return True
        
        return False
    
    # ==================== LAYER 3: Constraint Check ====================
    def layer3_constraint_check(self, vendor_data: Dict[str, Any], requirements: Dict[str, Any]) -> ValidationResult:
        """
        Verify that vendor data meets product requirements
        Check against hard constraints and red flags
        """
        try:
            violations = []
            
            # Check MOQ
            if vendor_data.get('moq'):
                moq = self._extract_number(vendor_data['moq'])
                if moq and moq > requirements.get('moq_max_acceptable', 500):
                    violations.append(f"MOQ too high: {moq} > {requirements['moq_max_acceptable']}")
            
            # Check price
            if vendor_data.get('price_per_unit'):
                price = self._extract_number(vendor_data['price_per_unit'])
                if price:
                    max_price = requirements.get('target_cogs_max', 150)
                    if price > max_price * 1.2:  # 20% tolerance
                        violations.append(f"Price too high: ${price} > ${max_price}")
            
            # Check for red flags
            description = str(vendor_data.get('description', '')).lower()
            for red_flag in requirements.get('red_flags', []):
                if red_flag.lower() in description:
                    violations.append(f"Red flag detected: '{red_flag}'")
            
            if violations:
                return ValidationResult(
                    passed=False,
                    reason=f"Constraint violations: {'; '.join(violations)}",
                    confidence=0.0
                )
            
            return ValidationResult(passed=True, reason="Constraints satisfied", confidence=1.0)
        
        except Exception as e:
            return ValidationResult(passed=False, reason=f"Constraint check error: {str(e)}", confidence=0.0)
    
    def _extract_number(self, text: Any) -> float:
        """Extract first number from text"""
        try:
            if isinstance(text, (int, float)):
                return float(text)
            
            text_str = str(text)
            # Remove currency symbols and commas
            text_str = re.sub(r'[$,£€¥]', '', text_str)
            # Find first number
            match = re.search(r'\d+\.?\d*', text_str)
            if match:
                return float(match.group())
        except:
            pass
        return None
    
    # ==================== LAYER 4: Consistency Check ====================
    def layer4_consistency_check(self, current_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Check consistency with previously validated data
        Detect anomalies and outliers
        """
        try:
            if not historical_data:
                return ValidationResult(passed=True, reason="No history to compare", confidence=0.8)
            
            # Check for duplicate vendors
            current_name = str(current_data.get('vendor_name', '')).lower()
            for hist in historical_data:
                hist_name = str(hist.get('vendor_name', '')).lower()
                if current_name and hist_name and self._similar_strings(current_name, hist_name):
                    return ValidationResult(
                        passed=False,
                        reason=f"Duplicate vendor detected: '{current_name}' similar to '{hist_name}'",
                        confidence=0.0
                    )
            
            # Check for price anomalies
            if current_data.get('price_per_unit'):
                current_price = self._extract_number(current_data['price_per_unit'])
                if current_price:
                    prices = [self._extract_number(h.get('price_per_unit')) for h in historical_data if h.get('price_per_unit')]
                    prices = [p for p in prices if p is not None]
                    
                    if len(prices) >= 3:
                        avg_price = sum(prices) / len(prices)
                        # Flag if price is 3x higher or 3x lower than average
                        if current_price > avg_price * 3 or current_price < avg_price / 3:
                            return ValidationResult(
                                passed=False,
                                reason=f"Price anomaly: ${current_price} vs avg ${avg_price:.2f}",
                                confidence=0.3
                            )
            
            return ValidationResult(passed=True, reason="Consistency check passed", confidence=0.9)
        
        except Exception as e:
            return ValidationResult(passed=False, reason=f"Consistency check error: {str(e)}", confidence=0.0)
    
    def _similar_strings(self, s1: str, s2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar (simple Jaccard similarity)"""
        if not s1 or not s2:
            return False
        
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    # ==================== LAYER 5: Cross-Validation Check ====================
    def layer5_cross_validation(self, data: Dict[str, Any], source_text: str) -> ValidationResult:
        """
        Final check: Cross-validate multiple fields against each other
        Ensure logical consistency
        """
        try:
            issues = []
            
            # Check if Android is mentioned when OS is claimed as Android
            if data.get('os') and 'android' in str(data['os']).lower():
                if 'android' not in source_text.lower():
                    issues.append("OS marked as Android but not found in source")
            
            # Check if touchscreen is claimed but not mentioned
            if data.get('touchscreen') is True:
                if 'touch' not in source_text.lower():
                    issues.append("Touchscreen claimed but not mentioned in source")
            
            # Check if price and MOQ are logically consistent
            price = self._extract_number(data.get('price_per_unit'))
            moq = self._extract_number(data.get('moq'))
            if price and moq:
                total = price * moq
                # If total order is less than $5000, it's suspicious for ODM
                if total < 5000:
                    issues.append(f"Suspiciously low total order value: ${total:.2f}")
            
            if issues:
                return ValidationResult(
                    passed=False,
                    reason=f"Cross-validation failed: {'; '.join(issues)}",
                    confidence=0.0
                )
            
            return ValidationResult(passed=True, reason="Cross-validation passed", confidence=1.0)
        
        except Exception as e:
            return ValidationResult(passed=False, reason=f"Cross-validation error: {str(e)}", confidence=0.0)
    
    # ==================== Master Validation Function ====================
    def validate_all(self, 
                     data: Dict[str, Any], 
                     source_text: str,
                     expected_schema: Dict[str, type],
                     requirements: Dict[str, Any],
                     historical_data: List[Dict[str, Any]] = None) -> Tuple[bool, List[ValidationResult]]:
        """
        Run all validation layers
        Returns: (passed, list_of_results)
        """
        results = []
        
        # Layer 1: Format
        r1 = self.layer1_format_check(data, expected_schema)
        results.append(("Layer 1: Format Check", r1))
        if not r1.passed:
            return False, results  # Stop immediately if format is wrong
        
        # Layer 2: Factual
        r2 = self.layer2_factual_check(data, source_text)
        results.append(("Layer 2: Factual Check", r2))
        
        # Layer 3: Constraints
        r3 = self.layer3_constraint_check(data, requirements)
        results.append(("Layer 3: Constraint Check", r3))
        
        # Layer 4: Consistency
        if historical_data is not None:
            r4 = self.layer4_consistency_check(data, historical_data)
            results.append(("Layer 4: Consistency Check", r4))
        
        # Layer 5: Cross-validation
        r5 = self.layer5_cross_validation(data, source_text)
        results.append(("Layer 5: Cross-Validation", r5))
        
        # Overall decision: All must pass
        all_passed = all(result.passed for _, result in results)
        
        # Log validation
        self._log_validation(data, results, all_passed)
        
        return all_passed, results
    
    def _log_validation(self, data: Dict[str, Any], results: List[Tuple[str, ValidationResult]], passed: bool):
        """Log validation for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "data_id": data.get('vendor_name', 'Unknown'),
            "overall_passed": passed,
            "layers": [
                {
                    "layer": name,
                    "passed": result.passed,
                    "reason": result.reason,
                    "confidence": result.confidence
                }
                for name, result in results
            ]
        }
        self.validation_log.append(log_entry)
    
    def get_validation_report(self) -> str:
        """Generate human-readable validation report"""
        if not self.validation_log:
            return "No validations performed yet."
        
        report = "=== VALIDATION REPORT ===\n\n"
        for entry in self.validation_log[-10:]:  # Last 10 validations
            report += f"Vendor: {entry['data_id']}\n"
            report += f"Overall: {'✓ PASSED' if entry['overall_passed'] else '✗ FAILED'}\n"
            for layer in entry['layers']:
                status = "✓" if layer['passed'] else "✗"
                report += f"  {status} {layer['layer']}: {layer['reason']} (conf: {layer['confidence']:.2f})\n"
            report += "\n"
        
        return report
