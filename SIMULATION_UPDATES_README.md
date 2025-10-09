# Updated Bike Shop Simulation Parameters

**Generated**: September 24, 2025  
**Version**: Latest with AI Competitors & Enhanced Features

## What's New in This Version

### 🤖 AI Competitor System
- **New File**: `konkurrenten.xlsx` - Complete AI competitor configuration
- **4 AI Competitors** with different strategies:
  - **BudgetCycles GmbH**: Cheap-only strategy (70% budget segment)
  - **CycleTech Solutions**: Balanced approach (40/40/20 split)
  - **PremiumWheels AG**: Premium-focused (60% premium segment)
  - **E-Motion Bikes**: E-bike specialist (80% e-bike focus)
- **Dynamic Market Competition**: AI competitors adapt strategies monthly
- **Market Saturation Effects**: Supply/demand balance affects prices

### 💰 Enhanced Financial Options
- **New Credit Option**: Sofortkredit (€15,000, 12.9% interest, 12 months)
- **Transport Cost System**: Distance-based pricing with 3 service levels
- **Updated Fixed Costs**: Realistic monthly operational expenses

### 🚴 Enhanced Bike Configuration
- **New Premium Bike**: E-Mountain-Bike with high-performance components
- **Quality Matching System**: Components must match bike segment quality
- **Flexible Component Requirements**: Bikes can use multiple compatible components

### 📊 Advanced Market Dynamics
- **Monthly Volume Capacity**: Markets have realistic demand limits
- **Price Sensitivity**: Different sensitivity per market/bike type
- **Seasonal Effects**: Market demand fluctuates based on seasonality

### 🏭 Enhanced Production System
- **Quality Upgrades**: Using premium components for standard bikes
- **Inventory Aging**: Older inventory sells at reduced prices
- **Production Efficiency**: R&D can improve manufacturing speed

## File Contents Overview

### Core Configuration Files
1. **fahrraeder.xlsx**: 7 bike types including premium E-Mountain-Bike
2. **lieferanten.xlsx**: 4 suppliers with quality levels (Basic/Standard/Premium)  
3. **preise_verkauf.xlsx**: Selling prices for all bike types in 3 segments
4. **lager.xlsx**: 4 warehouse locations with realistic capacity limits
5. **maerkte.xlsx**: 5 markets with demand patterns and price sensitivity
6. **personal.xlsx**: Worker types and wage rates
7. **finanzen.xlsx**: Starting capital, 4 credit options, fixed costs, transport rates

### New AI Competition File
8. **konkurrenten.xlsx**: Complete AI competitor system configuration
   - Competitor profiles and strategies
   - Market dynamics parameters  
   - Bike type preferences by strategy
   - Strategy behavior definitions

## Key Improvements

### 🎯 Realistic Simulation Parameters
- **Balanced Economics**: All prices and costs tested for gameplay balance
- **Quality Tiers**: Basic/Standard/Premium quality affects both cost and sales
- **Market Realism**: Demand patterns based on realistic bike market data

### ⚡ Performance Optimized
- **Reduced Warehouse Sizes**: More manageable inventory levels
- **Lower Transport Costs**: €0.10/km instead of €0.50/km for better gameplay
- **Optimized Demand**: Market demands scaled for engaging competition

### 🔧 Technical Enhancements  
- **JSON Component Requirements**: Flexible bike-component matching system
- **Quality Compatibility**: Automatic quality validation during production
- **Inventory Management**: Age tracking with price penalties

## Installation Instructions

1. Download the `updated_simulation_parameters_YYYYMMDD.zip` file
2. Extract all 8 XLSX files to your simulation directory
3. Upload through the simulation's parameter upload interface
4. Start a new game session to use the enhanced features

## Compatibility

- **Required**: Django Bike Shop Simulation v2.0+
- **Database**: Supports both SQLite and PostgreSQL
- **Features**: All legacy features maintained, new features added seamlessly

---

*Generated automatically by the Bike Shop Simulation Parameter Generator*