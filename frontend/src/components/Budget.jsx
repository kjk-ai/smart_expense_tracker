import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { transactionService } from '../services/transactionService';
import { budgetService } from '../services/budgetService';
import {
  Target,
  AlertTriangle,
  CheckCircle,
  Plus,
  Edit2,
  Trash2,
  X
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const Budget = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [budgets, setBudgets] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [formData, setFormData] = useState({
    category: '',
    amount: '',
    period: 'monthly'
  });

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    }
  }, [loading, user, navigate]);

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    try {
      setLoadingData(true);
      const [transactionsResponse, budgetsResponse] = await Promise.all([
        transactionService.getAllTransactions(),
        budgetService.getAllBudgets()
      ]);
      
      setTransactions(transactionsResponse.data);
      setBudgets(budgetsResponse.data);
    } catch (error) {
      console.error('Error fetching budget data:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const getCategorySpending = (category) => {
    const categoryTransactions = transactions.filter(
      transaction => transaction.category === category && transaction.type === 'expense'
    );
    
    return categoryTransactions.reduce((sum, transaction) => sum + transaction.amount, 0);
  };

  const getBudgetProgress = (budget) => {
    const spending = getCategorySpending(budget.category);
    const amount = parseFloat(budget.amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      return 0;
    }
    return Math.min((spending / amount) * 100, 100);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const budgetData = {
        ...formData,
        amount: parseFloat(formData.amount)
      };

      if (editingBudget) {
        await budgetService.updateBudget(editingBudget.id, budgetData);
      } else {
        await budgetService.createBudget(budgetData);
      }

      setIsModalOpen(false);
      setEditingBudget(null);
      setFormData({
        category: '',
        amount: '',
        period: 'monthly'
      });
      fetchData();
    } catch (error) {
      console.error('Error saving budget:', error);
    }
  };

  const handleEdit = (budget) => {
    setEditingBudget(budget);
    setFormData({
      category: budget.category,
      amount: budget.amount.toString(),
      period: budget.period || 'monthly'
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this budget?')) {
      try {
        await budgetService.deleteBudget(id);
        fetchData();
      } catch (error) {
        console.error('Error deleting budget:', error);
      }
    }
  };

  const openAddModal = () => {
    setEditingBudget(null);
    setFormData({
      category: '',
      amount: '',
      period: 'monthly'
    });
    setIsModalOpen(true);
  };

  // Prepare data for chart
  const chartData = budgets.map(budget => {
    const spending = getCategorySpending(budget.category);
    const remaining = budget.amount - spending;
    
    return {
      category: budget.category,
      budget: budget.amount,
      spent: spending,
      remaining: remaining
    };
  });

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Budget Planner</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Set spending limits and track your progress
          </p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Budget</span>
        </button>
      </div>

      {/* Budget Overview Chart */}
      {!loadingData && budgets.length > 0 && (
        <div className="p-6 rounded-xl border bg-white dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Budget Overview
            </h2>
            <Target className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" dark:stroke="#374151" />
              <XAxis dataKey="category" stroke="#6b7280" dark:stroke="#9ca3af" />
              <YAxis stroke="#6b7280" dark:stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  dark: {
                    backgroundColor: '#1f2937',
                    borderColor: '#374151',
                    color: '#f3f4f6'
                  },
                  borderColor: '#e5e7eb',
                  color: '#111827'
                }}
              />
              <Bar dataKey="spent" fill="#ef4444" name="Spent" />
              <Bar dataKey="remaining" fill="#10b981" name="Remaining" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Budget Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {!loadingData && budgets.length > 0 ? (
          budgets.map((budget) => {
            const spending = getCategorySpending(budget.category);
            const remaining = budget.amount - spending;
            const progress = getBudgetProgress(budget);
            const isOverBudget = progress > 100;
            const isNearBudget = progress >= 80 && !isOverBudget;
            const progressPercentage = Math.min(Math.max(progress, 0), 100);

            return (
              <div
                key={budget.id}
                className={`p-6 rounded-xl border ${
                  isOverBudget
                    ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
                    : isNearBudget
                    ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20'
                    : 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {budget.category}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {budget.period === 'monthly' ? 'Monthly' : 'Weekly'} Budget
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEdit(budget)}
                      className="p-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(budget.id)}
                      className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {isOverBudget ? 'Over Budget' : 'Remaining'}
                      </p>
                      <p className={`text-2xl font-bold ${
                        isOverBudget
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-green-600 dark:text-green-400'
                      }`}>
                        ${Math.abs(remaining).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Budget</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        ${budget.amount.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-400">Spent: ${spending.toFixed(2)}</span>
                      <span className={`font-medium ${
                        isOverBudget ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'
                      }`}>
                        {progress.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          isOverBudget
                            ? 'bg-red-500'
                            : isNearBudget
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: progressPercentage + '%' }}
                      ></div>
                    </div>
                  </div>

                  {isOverBudget && (
                    <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-sm font-medium">Over budget!</span>
                    </div>
                  )}

                  {isNearBudget && (
                    <div className="flex items-center space-x-2 text-yellow-600 dark:text-yellow-400">
                      <Target className="w-4 h-4" />
                      <span className="text-sm font-medium">Approaching budget</span>
                    </div>
                  )}

                  {!isOverBudget && !isNearBudget && progress > 0 && (
                    <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm font-medium">On track</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Target className="w-8 h-8 text-gray-400" />
            </div>
            <p>No budgets set</p>
            <p className="text-sm mt-1">Start by creating your first budget to track spending</p>
          </div>
        )}
      </div>

      {/* Add/Edit Budget Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {editingBudget ? 'Edit Budget' : 'Add Budget'}
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="">Select category</option>
                  <option value="Food">Food</option>
                  <option value="Transportation">Transportation</option>
                  <option value="Housing">Housing</option>
                  <option value="Entertainment">Entertainment</option>
                  <option value="Shopping">Shopping</option>
                  <option value="Health">Health</option>
                  <option value="Education">Education</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Budget Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Period
                </label>
                <select
                  value={formData.period}
                  onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 px-4 py-2 text-gray-700 dark:text-gray-300 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  {editingBudget ? 'Save Changes' : 'Add Budget'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Budget;