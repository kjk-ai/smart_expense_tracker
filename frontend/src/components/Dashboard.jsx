import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { transactionService } from '../services/transactionService';
import { holidayService } from '../services/holidayService';
import {
  PieChart as PieChartIcon,
  TrendingUp,
  TrendingDown,
  CreditCard,
  Calendar,
  Plus
} from 'lucide-react';
import { DayPicker } from 'react-day-picker';
import 'react-day-picker/dist/style.css';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid
} from 'recharts';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [holidayMonth, setHolidayMonth] = useState(new Date());
  const [holidays, setHolidays] = useState([]);
  const [holidayInsights, setHolidayInsights] = useState([]);
  const [holidayLoading, setHolidayLoading] = useState(false);
  const [holidayError, setHolidayError] = useState('');

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    }
  }, [loading, user, navigate]);

  useEffect(() => {
    if (user) {
      fetchData();
      fetchHolidayInsights();
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchHolidaysForMonth(holidayMonth);
    }
  }, [user, holidayMonth]);

  const fetchData = async () => {
    try {
      setLoadingData(true);
      const [transactionsResponse, statsResponse] = await Promise.all([
        transactionService.getAllTransactions(),
        transactionService.getTransactionStats()
      ]);
      
      setTransactions(transactionsResponse.data);
      const statsData = statsResponse.data || {};
      const monthlySummary = statsData.monthly_summary || {};
      const monthlyData = Object.entries(monthlySummary).map(([month, values]) => ({
        month,
        income: values?.income ?? 0,
        expenses: values?.expenses ?? 0
      }));

      setStats({
        totalIncome: statsData.total_income ?? 0,
        totalExpenses: statsData.total_expenses ?? 0,
        netIncome: statsData.net_income ?? 0,
        transactionsCount: statsData.transactions_count ?? 0,
        averageTransactionAmount: statsData.average_transaction_amount ?? 0,
        categoryBreakdown: statsData.category_breakdown ?? {},
        monthlyData
      });
      
      // Process category data for pie chart
      const categoryMap = {};
      transactionsResponse.data.forEach(transaction => {
        if (transaction.type === 'expense') {
          categoryMap[transaction.category] = (categoryMap[transaction.category] || 0) + transaction.amount;
        }
      });
      
      const categoryData = Object.entries(categoryMap).map(([category, amount]) => ({
        name: category,
        value: amount
      }));
      
      setCategories(categoryData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const getMonthRange = (monthDate) => {
    const start = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
    const end = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
    return { start, end };
  };

  const formatDate = (dateValue) => {
    const year = dateValue.getFullYear();
    const month = String(dateValue.getMonth() + 1).padStart(2, '0');
    const day = String(dateValue.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const fetchHolidaysForMonth = async (monthDate) => {
    try {
      setHolidayError('');
      const { start, end } = getMonthRange(monthDate);
      const response = await holidayService.getHolidays({
        country: user?.country_code,
        from: formatDate(start),
        to: formatDate(end)
      });
      setHolidays(response.data || []);
    } catch (error) {
      console.error('Error fetching holidays:', error);
      setHolidayError('Unable to load holidays.');
    }
  };

  const fetchHolidayInsights = async () => {
    try {
      setHolidayLoading(true);
      setHolidayError('');
      const response = await holidayService.getHolidayInsights({ windowDays: 30 });
      setHolidayInsights(response.data || []);
    } catch (error) {
      console.error('Error fetching holiday insights:', error);
      setHolidayError('Unable to load holiday insights.');
    } finally {
      setHolidayLoading(false);
    }
  };

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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Welcome back, {user.name}!</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Here's your financial overview for {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </p>
        </div>
        <Link
          to="/transactions"
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Transaction</span>
        </Link>
      </div>

      {/* Stats Cards */}
      {!loadingData && stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className={`p-6 rounded-xl border ${
            stats.netIncome >= 0 ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20' : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${stats.netIncome >= 0 ? 'text-green-800 dark:text-green-400' : 'text-red-800 dark:text-red-400'}`}>
                  Net Income
                </p>
                <p className="text-2xl font-bold mt-1 text-gray-900 dark:text-white">
                  ${stats.netIncome.toFixed(2)}
                </p>
              </div>
              {stats.netIncome >= 0 ? (
                <TrendingUp className={`w-8 h-8 ${stats.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`} />
              ) : (
                <TrendingDown className={`w-8 h-8 ${stats.netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`} />
              )}
            </div>
          </div>

          <div className="p-6 rounded-xl border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-800 dark:text-blue-400">
                  Total Income
                </p>
                <p className="text-2xl font-bold mt-1 text-gray-900 dark:text-white">
                  ${stats.totalIncome.toFixed(2)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="p-6 rounded-xl border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-400">
                  Total Expenses
                </p>
                <p className="text-2xl font-bold mt-1 text-gray-900 dark:text-white">
                  ${stats.totalExpenses.toFixed(2)}
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-600" />
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Pie Chart */}
        <div className="p-6 rounded-xl border bg-white dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Expenses by Category
            </h2>
            <PieChartIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </div>
          {loadingData ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          ) : categories.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categories}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'][index % 6]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <CreditCard className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              <p>No expense data available</p>
              <p className="text-sm mt-1">Add your first expense to see category breakdown</p>
            </div>
          )}
        </div>

        {/* Monthly Trend Chart */}
        <div className="p-6 rounded-xl border bg-white dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Monthly Trends
            </h2>
            <Calendar className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </div>
          {loadingData ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          ) : transactions.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats?.monthlyData || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" dark:stroke="#374151" />
                <XAxis dataKey="month" stroke="#6b7280" dark:stroke="#9ca3af" />
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
                <Legend />
                <Line type="monotone" dataKey="income" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
                <Line type="monotone" dataKey="expenses" stroke="#ef4444" strokeWidth={2} dot={{ fill: '#ef4444' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              <p>No transaction data available</p>
              <p className="text-sm mt-1">Start tracking your income and expenses</p>
            </div>
          )}
        </div>
      </div>

      {/* Holiday Calendar & Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-xl border bg-white dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Holiday Calendar
            </h2>
            <Calendar className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </div>
          {holidayError ? (
            <p className="text-sm text-red-600 dark:text-red-400">{holidayError}</p>
          ) : (
            <DayPicker
              mode="single"
              month={holidayMonth}
              onMonthChange={setHolidayMonth}
              modifiers={{
                holiday: holidays.map(item => new Date(item.date))
              }}
              modifiersStyles={{
                holiday: {
                  backgroundColor: '#dbeafe',
                  color: '#1e40af',
                  borderRadius: '6px'
                }
              }}
            />
          )}
          {holidays.length > 0 && (
            <div className="mt-4 space-y-2">
              {holidays.map((holiday) => (
                <div key={holiday.id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300">{holiday.name}</span>
                  <span className="text-gray-500 dark:text-gray-400">
                    {new Date(holiday.date).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
          {holidays.length === 0 && !holidayError && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">No holidays in this month.</p>
          )}
        </div>

        <div className="p-6 rounded-xl border bg-white dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Upcoming Holiday Insights
            </h2>
          </div>
          {holidayLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
            </div>
          ) : holidayInsights.length > 0 ? (
            <div className="space-y-4">
              {holidayInsights.map((insight) => (
                <div key={insight.holiday_event_id} className="p-4 border rounded-lg dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{insight.holiday_name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(insight.holiday_date).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      insight.confidence === 'high'
                        ? 'bg-green-100 text-green-700'
                        : insight.confidence === 'medium'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {insight.confidence} confidence
                    </span>
                  </div>
                  {insight.status === 'insufficient_data' ? (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{insight.explanation}</p>
                  ) : (
                    <>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                        Expected change: {insight.expected_change_pct >= 0 ? '+' : ''}{insight.expected_change_pct}%
                      </p>
                      {insight.recommended_adjustment_pct > 0 && (
                        <p className="text-sm text-primary-600 dark:text-primary-400 mt-1">
                          Recommended pre-adjustment: reduce spending by {insight.recommended_adjustment_pct}% this week
                        </p>
                      )}
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{insight.explanation}</p>
                    </>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No upcoming holiday insights yet.
            </p>
          )}
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="p-6 rounded-xl border bg-white dark:bg-gray-800 dark:border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Transactions
          </h2>
          <Link
            to="/transactions"
            className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-sm font-medium"
          >
            View All
          </Link>
        </div>

        {loadingData ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : transactions.length > 0 ? (
          <div className="space-y-4">
            {transactions.slice(0, 5).map((transaction) => (
              <div
                key={transaction.id}
                className="flex items-center justify-between p-4 rounded-lg border dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    transaction.type === 'income' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
                  }`}>
                    {transaction.type === 'income' ? (
                      <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{transaction.description}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {transaction.category} • {new Date(transaction.date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className={`font-bold ${
                  transaction.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {transaction.type === 'income' ? '+' : '-'}$
                  {transaction.amount.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <CreditCard className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p>No transactions yet</p>
            <p className="text-sm mt-1">Start tracking your financial activity</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
