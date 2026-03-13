"""
Provider Schema Registry - Intelligence Layer Foundation
Creates structured schemas for all target API providers with their credit discovery endpoints,
free tier details, and monitoring requirements.
"""
import json
from datetime import datetime
from typing import Dict, Any, List
import logging
from firebase_init import firebase_manager

logger = logging.getLogger(__name__)

class ProviderSchemaCreator:
    """Creates and manages provider schemas in Firestore"""
    
    def __init__(self):
        self.db = firebase_manager.get_firestore()
        
    def create_provider_schemas(self) -> Dict[str, int]:
        """
        Creates comprehensive provider schemas in Firestore
        
        Returns:
            Dict with provider counts and status
        """
        providers = self._build_provider_data()
        results = {'created': 0, 'updated': 0, 'errors': 0}
        
        for provider_id, schema in providers.items():
            try:
                doc_ref = self.db.collection('provider_schemas').document(provider_id)
                
                # Check if exists
                existing = doc_ref.get()
                if existing.exists:
                    # Update with merge
                    doc_ref.set(schema, merge=True)
                    results['updated'] += 1
                    logger.info(f"Updated schema for {provider_id}")
                else:
                    # Create new
                    doc_ref.set(schema)
                    results['created'] += 1
                    logger.info(f"Created schema for {provider_id}")
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Error creating schema for {provider_id}: {e}")
        
        logger.info(f"Schema creation complete: {results}")
        return results
    
    def _build_provider_data(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive provider schema data"""
        
        # Base template for all providers
        base_schema = {
            'created_at': firestore.SERVER_TIMESTAMP,
            'last_updated': firestore.SERVER_TIMESTAMP,
            'schema_version': '1.0.0',
            'monitoring_enabled': True,
            'legal_boundary': 'TOOL_NOT_SERVICE'
        }
        
        providers = {
            'aws': {
                **base_schema,
                'display_name': 'Amazon Web Services',
                'credit_endpoints': [
                    {
                        'id': 'aws_cost_explorer',
                        'type': 'boto3',
                        'service': 'ce',
                        'operation': 'get_cost_and_usage',
                        'parameters': {
                            'Granularity': 'MONTHLY',
                            'Metrics': ['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                            'Filter': {
                                'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Credit']}
                            }
                        },
                        'required_iam_permissions': ['ce:GetCostAndUsage'],
                        'check_interval_hours': 24
                    },
                    {
                        'id': 'aws_billing_conductor',
                        'type': 'boto3',
                        'service': 'billingconductor',
                        'operation': 'list_billing_group_cost_reports',
                        'required_iam_permissions': ['billingconductor:ListBillingGroupCostReports'],
                        'check_interval_hours': 168  # Weekly
                    }
                ],
                'free_tier_metrics': {
                    'lambda': {
                        'monthly_free_requests': 1000000,
                        'compute_time_gb_seconds': 400000,
                        'description': 'AWS Lambda Free Tier'
                    },
                    'ec2': {
                        't2_micro_hours': 750,
                        'description': '750 hours of t2.micro per month'
                    },
                    's3': {
                        'standard_storage_gb': 5,
                        'put_requests': 2000,
                        'get_requests': 20000
                    }
                },
                'adversarial_flags': [
                    'unusual_cost_spike',
                    'multiple_region_activation',
                    'rapid_credential_rotation',
                    'concurrent_session_limit'
                ],
                'circuit_breaker_thresholds': {
                    'error_rate_percent': 10,
                    'consecutive_failures': 3,
                    'anomaly_score': 0.7
                }
            },
            
            'openai': {
                **base_schema,
                'display_name': 'OpenAI API',
                'credit_endpoints': [
                    {
                        'id': 'openai_usage',
                        'type': 'openai',
                        'endpoint': 'https://api.openai.com/v1/usage',
                        'method': 'GET',
                        'parameters': {'date': '{current_date}'},
                        'required_scopes': ['usage:read'],
                        'check_interval_hours': 6
                    }
                ],
                'free_tier_metrics': {
                    'api_credits': {
                        'initial_credits': 18.0,
                        'currency': 'USD',
                        'description': 'Free trial credits'
                    }
                }
            },
            
            'google_cloud': {
                **base_schema,
                'display_name': 'Google Cloud Platform',
                'credit_endpoints': [
                    {
                        'id': 'gcp_billing',
                        'type': 'google.cloud.billing',
                        'service': 'CloudBillingClient',
                        'operation': 'get_billing_account',
                        'required_permissions': ['billing.accounts.get'],
                        'check_interval_hours': 24
                    }
                ],
                'free_tier_metrics': {
                    'always_free': {
                        'compute_engine': '1 f1-micro instance per month',
                        'cloud_storage': '5GB per month',
                        'cloud_functions': '2 million invocations per month'
                    },
                    'free_trial': {
                        'credits': 300,
                        'currency': 'USD',
                        'duration_days': 90
                    }
                }
            },
            
            'twilio': {
                **base_schema,
                'display_name': 'Twilio',
                'credit_endpoints': [
                    {
                        'id': 'twilio_balance',
                        'type': 'twilio',
                        'operation': 'fetch_balance',
                        'required_scopes': ['balance:read'],
                        'check_interval_hours': 12
                    }
                ],
                'free_tier_metrics': {
                    'trial_credits': {
                        'amount': 15.0,
                        'currency': 'USD',
                        'verification_required': True
                    }
                }
            },
            
            'azure':