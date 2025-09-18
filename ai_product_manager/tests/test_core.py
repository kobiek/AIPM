"""Tests for the core AI Product Manager functionality."""
import pytest
from datetime import datetime
from ai_product_manager.core import Product, Feature, AIProductManager

def test_create_product():
    """Test creating a new product."""
    product = Product(
        id="test-001",
        name="Test Product",
        description="A test product",
        target_market="Testers"
    )
    
    assert product.id == "test-001"
    assert product.name == "Test Product"
    assert product.description == "A test product"
    assert product.target_market == "Testers"
    assert isinstance(product.created_at, datetime)
    assert isinstance(product.updated_at, datetime)

def test_add_feature():
    """Test adding a feature to the product manager."""
    product = Product("test-001", "Test Product", "A test product", "Testers")
    pm = AIProductManager(product)
    
    feature = Feature(
        id="f1",
        name="Test Feature",
        description="A test feature",
        status="backlog",
        priority=1,
        effort_estimate=3,
        value_score=8
    )
    
    pm.add_feature(feature)
    
    assert len(pm.features) == 1
    assert "f1" in pm.features
    assert pm.features["f1"].name == "Test Feature"

def test_prioritize_features():
    """Test feature prioritization."""
    product = Product("test-001", "Test Product", "A test product", "Testers")
    pm = AIProductManager(product)
    
    # Add features with different priorities and value scores
    features = [
        Feature(f"f{i}", f"Feature {i}", f"Description {i}", 
                priority=i % 3, 
                effort_estimate=(i % 3) + 1,
                value_score=10 - i)
        for i in range(1, 6)
    ]
    
    for feature in features:
        pm.add_feature(feature)
    
    # Get prioritized features
    prioritized = pm.prioritize_features()
    
    # Check that features are sorted by priority (descending) and value/effort ratio
    priorities = [f.priority for f in prioritized]
    assert priorities == sorted(priorities, reverse=True)
    
    # For features with same priority, higher value/effort ratio should come first
    for i in range(len(prioritized) - 1):
        if prioritized[i].priority == prioritized[i + 1].priority:
            ratio_i = prioritized[i].value_score / (prioritized[i].effort_estimate or 1)
            ratio_j = prioritized[i + 1].value_score / (prioritized[i + 1].effort_estimate or 1)
            assert ratio_i >= ratio_j

def test_generate_status_report():
    """Test generating a status report."""
    product = Product("test-001", "Test Product", "A test product", "Testers")
    pm = AIProductManager(product)
    
    # Add some features with different statuses
    features = [
        Feature(f"f{i}", f"Feature {i}", f"Description {i}", 
                status=status,
                priority=i % 3 + 1)
        for i, status in enumerate(["completed"] * 2 + ["in_progress"] * 3 + ["backlog"] * 5)
    ]
    
    for feature in features:
        pm.add_feature(feature)
    
    report = pm.generate_status_report()
    
    # Basic checks on the report content
    assert "Test Product" in report
    assert "2 completed" in report
    assert "3 in progress" in report
    assert "5 in backlog" in report
    assert "Top Priority Features" in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
