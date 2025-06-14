# 📊 **RIGHT PANEL DASHBOARD - API DATA STRUCTURE**

## 🎯 **CORE DASHBOARD API ENDPOINT**

### **Primary API Route**
```
POST /sbotchat/dashboard/realtime_stats
```

## 📋 **API RESPONSE STRUCTURE**

### **1. EMPLOYEE OVERVIEW**
```json
{
  "employee_overview": {
    "total_employees": 150,
    "active_employees": 148,
    "departments_count": 12,
    "today_checkins": 142,
    "attendance_rate": 94.7,
    "on_leave_today": 6,
    "late_arrivals": 8,
    "absent_today": 2,
    "overtime_workers": 15,
    "missing_checkout": 3
  }
}
```

### **2. REAL-TIME ATTENDANCE**
```json
{
  "realtime_attendance": {
    "last_updated": "2025-01-14T10:30:00Z",
    "recent_checkins": [
      {
        "employee_id": 123,
        "employee_name": "Nguyễn Văn A",
        "check_in": "08:15:00",
        "status": "late",
        "department": "IT",
        "expected_time": "08:00:00"
      },
      {
        "employee_id": 124,
        "employee_name": "Trần Thị B", 
        "check_in": "07:45:00",
        "status": "early",
        "department": "HR",
        "expected_time": "08:00:00"
      }
    ],
    "summary": {
      "total_today": 142,
      "early": 34,
      "on_time": 100,
      "late": 8,
      "absent": 2
    }
  }
}
```

### **3. LEAVE MANAGEMENT**
```json
{
  "leave_management": {
    "pending_approvals": {
      "count": 5,
      "requests": [
        {
          "leave_id": 456,
          "employee_name": "Nguyễn Văn D",
          "employee_id": 125,
          "leave_type": "Annual Leave",
          "date_from": "2025-01-15",
          "date_to": "2025-01-17",
          "days": 3,
          "reason": "Family vacation",
          "priority": "normal",
          "submitted_date": "2025-01-12"
        }
      ]
    },
    "approved_today": 3,
    "rejected_today": 1,
    "total_days_requested": 45,
    "most_used_leave_type": {
      "name": "Annual Leave",
      "count": 8
    }
  }
}
```

### **4. RECRUITMENT PIPELINE**
```json
{
  "recruitment": {
    "open_positions": {
      "count": 8,
      "urgent": 3,
      "positions": [
        {
          "job_id": 789,
          "title": "Senior Developer",
          "department": "IT",
          "applicants_count": 12,
          "status": "urgent",
          "deadline": "2025-01-31"
        }
      ]
    },
    "applicants": {
      "total": 23,
      "new": 5,
      "in_progress": 15,
      "hired_this_month": 2,
      "rejected": 3
    },
    "interviews_scheduled": {
      "today": 2,
      "this_week": 7
    }
  }
}
```

### **5. PAYROLL & FINANCE**
```json
{
  "payroll": {
    "current_month": {
      "payslips_generated": 120,
      "payslips_pending": 30,
      "total_salary_cost": 2500000000,
      "average_salary": 15000000
    },
    "insurance": {
      "active_policies": 148,
      "expiring_soon": 5,
      "total_premium": 450000000
    },
    "overtime": {
      "total_hours": 240,
      "cost": 180000000,
      "employees_count": 15
    }
  }
}
```

### **6. NOTIFICATIONS & ALERTS**
```json
{
  "notifications": {
    "high_priority": [
      {
        "type": "leave_approval",
        "message": "5 leave requests pending approval",
        "count": 5,
        "action_url": "/hr/leaves/pending"
      },
      {
        "type": "attendance_missing",
        "message": "3 employees haven't checked out",
        "count": 3,
        "action_url": "/hr/attendance/missing"
      }
    ],
    "medium_priority": [
      {
        "type": "contract_expiring",
        "message": "2 contracts expiring this month",
        "count": 2,
        "action_url": "/hr/contracts/expiring"
      }
    ],
    "total_unread": 8
  }
}
```

## 🔄 **REAL-TIME UPDATE MECHANISM**

### **WebSocket Events Structure**
```json
{
  "event_type": "dashboard_update",
  "timestamp": "2025-01-14T10:30:00Z",
  "data": {
    "section": "attendance", // attendance, leave, recruitment, payroll
    "update_type": "live", // live, periodic, manual
    "payload": {
      // Section-specific data update
    }
  }
}
```

### **Update Frequencies**
- **Real-time (WebSocket)**: Attendance check-ins/outs
- **Every 30s**: Dashboard stats refresh  
- **Every 5 minutes**: Leave requests, recruitment
- **Every 1 hour**: Payroll calculations
- **Manual trigger**: User actions

## 🎛️ **QUICK ACTIONS API STRUCTURE**

### **Quick Action Endpoints**
```json
{
  "quick_actions": [
    {
      "id": "approve_leaves",
      "title": "Duyệt nghỉ phép",
      "icon": "✅",
      "endpoint": "/sbotchat/quick_action/approve_leaves",
      "method": "POST",
      "permission": "hr.group_hr_manager"
    },
    {
      "id": "add_employee", 
      "title": "Thêm nhân viên",
      "icon": "👥",
      "endpoint": "/sbotchat/quick_action/add_employee",
      "method": "GET", 
      "permission": "hr.group_hr_user"
    },
    {
      "id": "generate_report",
      "title": "Xem báo cáo",
      "icon": "📊", 
      "endpoint": "/sbotchat/quick_action/generate_report",
      "method": "GET",
      "permission": "hr.group_hr_user"
    },
    {
      "id": "calculate_payroll",
      "title": "Tính lương",
      "icon": "💰",
      "endpoint": "/sbotchat/quick_action/calculate_payroll", 
      "method": "POST",
      "permission": "hr.group_hr_manager"
    }
  ]
}
```

## 📱 **RESPONSIVE & PERFORMANCE**

### **Data Optimization**
- **Pagination**: Max 10 items per list
- **Caching**: Redis cache cho 5 phút
- **Compression**: Gzip response
- **Lazy Loading**: Load charts on demand

### **Error Handling**
```json
{
  "success": false,
  "error": {
    "code": "DASHBOARD_ERROR",
    "message": "Unable to fetch attendance data",
    "details": "hr.attendance model access denied",
    "retry_after": 30
  },
  "fallback_data": {
    // Cached/default data khi có lỗi
  }
}
```

## 🔒 **SECURITY & PERMISSIONS**

### **Access Control**
- **Manager Level**: Toàn bộ dashboard
- **HR User**: Employee data + basic stats  
- **Employee**: Chỉ dữ liệu cá nhân
- **Guest**: Không truy cập

### **Data Filtering**
- Dữ liệu được filter theo company_id
- Multi-tenant support
- Department-based restrictions
- GDPR compliance cho personal data 