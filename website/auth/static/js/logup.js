
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');
const signup = document.getElementById('signup-button');
const login = document.getElementById('login-button');

signUpButton.addEventListener('click', () => {
	container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
	container.classList.remove("right-panel-active");
});


//------------------Signup Validation
const form = document.getElementById('signup-form');
const username = document.getElementById('username');
const email = document.getElementById('email');
const phone = document.getElementById('phone');
const password = document.getElementById('password');
const password2 = document.getElementById('password2');
const valid = document.getElementById('signup-button');
const sub = document.getElementById('form-submit');

valid.addEventListener('click', function(){
	checkInputs();
});

function checkInputs() {
	// trim to remove the whitespaces
	const usernameValue = username.value.trim();
	const emailValue = email.value.trim();
	const phoneValue = phone.value.trim();
	const passwordValue = password.value.trim();
	const password2Value = password2.value.trim();
	
	var errors = [];

	if(usernameValue === '') {
		setErrorFor(username, 'Username cannot be blank');
		errors.push('u');
	} else {
		setSuccessFor(username);
	}
	
	if(emailValue === '') {
		setErrorFor(email, 'Email cannot be blank');
		errors.push('e');
	} else if (!isEmail(emailValue)) {
		setErrorFor(email, 'Not a valid email');
		errors.push('ea');
	} else {
		setSuccessFor(email);
	}

	if(phoneValue === '') {
		setErrorFor(phone, 'Phone cannot be blank');
		errors.push('p');
	} else {
		setSuccessFor(phone);
	}
	
	if(passwordValue === '') {
		setErrorFor(password, 'Password cannot be blank');
		errors.push('v');
	} else {
		setSuccessFor(password);
	}
	
	if(password2Value === '') {
		setErrorFor(password2, 'Password cannot be blank');
		errors.push('v1');
	} else if(passwordValue !== password2Value) {
		setErrorFor(password2, "Passwords don't match");
		errors.push('v2');
	} else{
		setSuccessFor(password2);
	}

	if(errors.length == 0){
		sub.click();
	} 
}

function setErrorFor(input, message) {
	const formControl = input.parentElement;
	const small = formControl.querySelector('small');
	formControl.className = 'form-control error';
	small.innerText = message;
}

function setSuccessFor(input) {
	const formControl = input.parentElement;
	formControl.className = 'form-control success';
}
	
function isEmail(email) {
	return /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(email);
}
