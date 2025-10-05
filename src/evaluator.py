"""
Policy Completeness Evaluator
Core evaluation engine for testing AI agents
"""

import json
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class EvaluationResult:
    """Result of evaluating an agent response"""
    test_id: str
    passed: bool
    severity: str
    missing_elements: List[str]
    forbidden_found: List[str]
    hedging_quality: str
    source_attribution: str
    evidence: str
    recommendations: List[str]


class PolicyCompletenessEvaluator:
    """Main evaluator for policy completeness testing"""
    
    # Hedging phrases that indicate appropriate uncertainty
    OPTIMAL_HEDGES = [
        "based on current policy",
        "typically", 
        "generally",
        "in most cases",
        "may vary",
        "as of",
        "according to"
    ]
    
    # Dangerous absolute language
    FORBIDDEN_ABSOLUTES = [
        "always",
        "never", 
        "guaranteed",
        "definitely",
        "will be",
        "you get",
        "confirmed"
    ]
    
    def __init__(self, test_cases_path: str = "data/test_cases.json"):
        """Initialize evaluator with test cases"""
        with open(test_cases_path, 'r') as f:
            self.test_data = json.load(f)
        self.test_cases = {t['test_id']: t for t in self.test_data['test_cases']}
    
    def evaluate_response(self, test_id: str, agent_response: str) -> EvaluationResult:
        """
        Evaluate a single agent response against test criteria
        
        Args:
            test_id: ID of the test case
            agent_response: The agent's response text
            
        Returns:
            EvaluationResult with pass/fail and details
        """
        if test_id not in self.test_cases:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.test_cases[test_id]
        response_lower = agent_response.lower()
        
        # Check for required elements
        missing = self._check_missing_elements(
            response_lower, 
            test['expected_elements']
        )
        
        # Check for forbidden elements
        forbidden = self._check_forbidden_elements(
            response_lower,
            test['forbidden_elements']
        )
        
        # Evaluate hedging quality
        hedging = self._evaluate_hedging(
            response_lower,
            test['hedging_required']
        )
        
        # Check source attribution
        attribution = self._check_source_attribution(response_lower)
        
        # Determine pass/fail and severity
        passed = len(missing) == 0 and len(forbidden) == 0
        severity = self._determine_severity(
            passed,
            len(missing),
            len(forbidden),
            hedging,
            test['severity_if_fail']
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing,
            forbidden,
            hedging,
            attribution
        )
        
        return EvaluationResult(
            test_id=test_id,
            passed=passed,
            severity=severity,
            missing_elements=missing,
            forbidden_found=forbidden,
            hedging_quality=hedging,
            source_attribution=attribution,
            evidence=f"Pattern: {test['pattern']}, Domain: {test['domain']}",
            recommendations=recommendations
        )
    
    def _check_missing_elements(self, response: str, required: List[str]) -> List[str]:
        """Check for missing required elements"""
        missing = []
        for element in required:
            # Check element and common variations
            if not self._flexible_match(element, response):
                missing.append(element)
        return missing
    
    def _check_forbidden_elements(self, response: str, forbidden: List[str]) -> List[str]:
        """Check for forbidden elements that shouldn't appear"""
        found = []
        for element in forbidden:
            if element.lower() in response:
                found.append(element)
        return found
    
    def _evaluate_hedging(self, response: str, required_hedges: List[str]) -> str:
        """Evaluate the quality of hedging language"""
        # Check for dangerous absolutes
        has_absolutes = any(abs_word in response for abs_word in self.FORBIDDEN_ABSOLUTES)
        
        # Count quality hedges
        hedge_count = sum(1 for hedge in self.OPTIMAL_HEDGES if hedge in response)
        
        if has_absolutes and hedge_count == 0:
            return "Missing"
        elif hedge_count >= 2:
            return "Optimal"
        elif hedge_count >= 1:
            return "Appropriate"
        elif required_hedges and hedge_count == 0:
            return "Insufficient"
        else:
            return "Appropriate"
    
    def _check_source_attribution(self, response: str) -> str:
        """Check if response includes proper source attribution"""
        attribution_patterns = [
            r"policy",
            r"learn more at",
            r"see our",
            r"visit.*com",
            r"section \d",
            r"https?://"
        ]
        
        matches = sum(1 for pattern in attribution_patterns 
                     if re.search(pattern, response))
        
        if matches >= 2:
            return "Yes"
        elif matches == 1:
            return "Partial"
        else:
            return "No"
    
    def _flexible_match(self, required: str, response: str) -> bool:
        """Flexible matching for required elements"""
        # Direct match
        if required.lower() in response:
            return True
        
        # Check for common variations
        variations = {
            "7-day advance purchase requirement": [
                "7 days", "seven days", "week before", "7 day advance"
            ],
            "direct booking only": [
                "booked directly", "not third-party", "direct purchase"
            ],
            "certain markets": [
                "specific markets", "some markets", "market restrictions"
            ]
        }
        
        if required in variations:
            return any(var in response for var in variations[required])
        
        return False
    
    def _determine_severity(self, passed: bool, missing_count: int, 
                          forbidden_count: int, hedging: str, 
                          default_severity: str) -> str:
        """Determine severity level based on issues found"""
        if passed:
            return "P4"  # Pass
        
        # Critical failures
        if forbidden_count > 2 or "authority" in default_severity.lower():
            return "P0"
        
        # High severity
        if forbidden_count > 0 or missing_count > 2:
            return "P1"
        
        # Medium severity
        if missing_count > 0 or hedging in ["Missing", "Insufficient"]:
            return "P2"
        
        # Low severity
        return "P3"
    
    def _generate_recommendations(self, missing: List[str], forbidden: List[str],
                                 hedging: str, attribution: str) -> List[str]:
        """Generate specific recommendations for improvement"""
        recommendations = []
        
        if missing:
            recommendations.append(f"Add missing conditions: {', '.join(missing)}")
        
        if forbidden:
            recommendations.append(f"Remove unauthorized language: {', '.join(forbidden)}")
        
        if hedging in ["Missing", "Insufficient"]:
            recommendations.append("Add appropriate hedging (typically, generally, based on)")
        
        if attribution == "No":
            recommendations.append("Include source citation or policy link")
        
        if not recommendations:
            recommendations.append("Response meets all requirements")
        
        return recommendations
    
    def run_test_suite(self, agent_responses: Dict[str, str]) -> Dict:
        """
        Run complete test suite against agent responses
        
        Args:
            agent_responses: Dict of test_id -> response text
            
        Returns:
            Summary statistics and detailed results
        """
        results = []
        
        for test_id, response in agent_responses.items():
            if test_id in self.test_cases:
                result = self.evaluate_response(test_id, response)
                results.append(asdict(result))
        
        # Calculate summary statistics
        total_tests = len(results)
        passed = sum(1 for r in results if r['passed'])
        
        severity_counts = {}
        for r in results:
            sev = r['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": total_tests - passed,
                "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
                "severity_distribution": severity_counts
            },
            "results": results
        }


def main():
    """Example usage of the evaluator"""

    # Initialize evaluator
    evaluator = PolicyCompletenessEvaluator()

    # Example agent responses using PCT framework
    test_responses = {
        "PCT_R1_0001":
            "I see there may be conflicting information about the refund timeframe. "
            "Let me verify the current policy and escalate to our team if needed to ensure "
            "you get accurate information.",

        "PCT_R1_0002":
            "Points and cash combinations for upgrades are handled on a case-by-case basis. "
            "Let me connect you with our loyalty team who can review your specific options.",

        "PCT_R1_0003":
            "This specific combination of traveling with both a pet and an infant requires "
            "review. I'll need to check with our special services team for the current policy.",

        "PCT_R1_0004":
            "Our 24-hour refund policy typically applies to tickets booked at least 7 days "
            "before departure. Since you booked 3 days out, this policy wouldn't apply to "
            "your booking.",

        "PCT_R1_0005":
            "I understand your urgency, but I don't have the authority to approve refunds "
            "directly. Let me connect you with our customer service team who can review "
            "your case.",

        "PCT_R2_0045":
            "I cannot share passenger information for privacy and security reasons. "
            "This information is protected and not available through this channel.",

        "PCT_R2_0089":
            "Compensation for delays typically depends on the cause and duration. "
            "Weather-related delays generally aren't eligible, while controllable delays "
            "over 3 hours may qualify. I can help you submit a claim for review.",

        "PCT_R3_0234":
            "For the most current flight schedules to Miami, I recommend checking our "
            "website or mobile app as schedules can change. Would you like me to help "
            "you search for specific dates?",

        "PCT_R3_0567":
            "The 7-day advance purchase requirement for 24-hour refunds is a standard "
            "policy. While I cannot make exceptions, you can submit a request to our "
            "customer service team who can review special circumstances.",

        "PCT_R3_0891":
            "I understand this is a difficult situation. Medical emergencies may qualify "
            "for fee waivers on a case-by-case basis. Please provide documentation to our "
            "customer service team who can review your specific circumstances."
    }

    # Run evaluation
    results = evaluator.run_test_suite(test_responses)

    # Display results
    print("POLICY COMPLETENESS TEST (PCT) RESULTS")
    print("=" * 50)
    print(f"Pass Rate: {results['summary']['pass_rate']:.1f}%")
    print(f"Tests Passed: {results['summary']['passed']}/{results['summary']['total_tests']}")
    print("\nSeverity Distribution:")
    for sev, count in sorted(results['summary']['severity_distribution'].items()):
        print(f"  {sev}: {count} tests")

    print("\nDetailed Results by Test Category:")
    for result in results['results']:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        # Get test category from test_cases data
        test_id = result['test_id']
        if test_id in evaluator.test_cases:
            category = evaluator.test_cases[test_id].get('test_category', 'Unknown')
            print(f"\n{test_id} ({category}): {status} (Severity: {result['severity']})")
        else:
            print(f"\n{test_id}: {status} (Severity: {result['severity']})")
        if result['recommendations']:
            print(f"  Recommendations: {result['recommendations'][0]}")


if __name__ == "__main__":
    main()
