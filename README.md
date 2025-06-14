# HR Chatbot - SBot Chat

🤖 **AI-Powered HR Assistant for Odoo 18.0**

An intelligent HR chatbot module powered by DeepSeek API that provides comprehensive HR management capabilities through natural language processing in both Vietnamese and English.

## ✨ Features

### 🧠 AI Chatbot Core
- **DeepSeek API Integration**: Supports both `deepseek-chat` and `deepseek-reasoner` models
- **Customizable API Settings**: Flexible configuration for different use cases
- **Real-time Chat Interface**: Modern, responsive chat UI
- **Conversation History**: Persistent chat history with sidebar navigation
- **Global Floating Access**: Quick access button available throughout the system

### 🏢 HR Assistant Integration
- **Natural Language Processing**: Handle HR requests in Vietnamese and English
- **116+ API Endpoints**: Complete HR system coverage
- **Smart Intent Recognition**: Automatic understanding of user requests
- **Auto Parameter Extraction**: Intelligent data extraction from conversations

### 📋 HR Management Capabilities
- **Employee Management**: Complete employee lifecycle management
- **Attendance Tracking**: Time tracking and attendance monitoring
- **Leave Management**: Holiday and leave request processing
- **Payroll Integration**: Salary and compensation management
- **Recruitment**: Hiring process automation
- **Skills Management**: Employee skills tracking and development
- **Project Management**: Project assignment and tracking
- **Insurance Management**: BHXH/BHYT/BHTN integration
- **Analytics & Reporting**: Comprehensive HR dashboards and statistics

## 🚀 Installation

### Prerequisites
- Odoo 18.0
- Python 3.8+
- DeepSeek API key

### Required Odoo Modules
```
base, web, mail, hr, hr_contract, hr_attendance, hr_holidays, 
hr_payroll_community, hr_recruitment, hr_skills, hr_timesheet,
hr_expense, hr_homeworking, project, calendar, fleet, analytic
```

### Installation Steps
1. Clone this repository to your Odoo addons directory:
   ```bash
   git clone https://github.com/daovinhkhang/HR_Chatbot.git
   ```

2. Update your Odoo addons path to include this module

3. Restart your Odoo server

4. Go to Apps → Update Apps List

5. Search for "SBot Chat" and install the module

6. Configure your DeepSeek API settings in the module configuration

## ⚙️ Configuration

1. **API Setup**: Configure your DeepSeek API credentials
2. **Model Selection**: Choose between `deepseek-chat` or `deepseek-reasoner`
3. **Language Settings**: Set preferred language (Vietnamese/English)
4. **HR Integration**: Ensure all required HR modules are installed and configured

## 🎯 Usage

### Accessing the Chatbot
- **Floating Button**: Click the floating chat button available on any page
- **Menu Access**: Navigate through the main menu to access chat history
- **Sidebar**: Use the conversation history sidebar to manage multiple chats

### HR Queries Examples
```
Vietnamese:
- "Tạo nhân viên mới tên Nguyễn Văn A"
- "Xem lịch sử chấm công tháng này"
- "Tạo đơn xin nghỉ phép 3 ngày"

English:
- "Create new employee John Doe"
- "Show attendance report for this month"
- "Submit leave request for 3 days"
```

## 🏗️ Project Structure

```
sbotchat/
├── controllers/          # HTTP controllers and API endpoints
├── models/              # Odoo models and business logic
├── security/            # Access rights and security rules
├── static/              # Frontend assets
│   ├── src/
│   │   ├── css/        # Stylesheets
│   │   ├── js/         # JavaScript files
│   │   └── xml/        # QWeb templates
├── tests/               # Unit and integration tests
├── views/               # XML view definitions
├── __init__.py          # Module initialization
└── __manifest__.py      # Module manifest
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the LGPL-3 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in this repository
- Contact: [Your Contact Information]

## 🔄 Version History

- **v1.0.0**: Initial release with full HR integration and DeepSeek API support

---

**Made with ❤️ for the Odoo Community** 